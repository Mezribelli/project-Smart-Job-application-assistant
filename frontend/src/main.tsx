import { FormEvent, useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

const API = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8080";
const AI_API = import.meta.env.VITE_AI_SERVICE_URL ?? "http://localhost:8000";

type Profile = {
  id?: number;
  fullName: string;
  email: string;
  phone?: string;
  professionalTitle?: string;
  preferredLocation?: string;
  education?: string;
  desiredEmploymentType?: string;
  yearsOfExperience?: number;
  skills: string[];
};

type Job = {
  id: number;
  title: string;
  company: string;
  location: string;
  employmentType?: string;
  description: string;
  skills: string[];
  status: string;
  minimumExperienceYears?: number;
};

type MatchResult = {
  score: number;
  matchingSkills: string[];
  missingSkills: string[];
  recommendation: string;
};

type Application = {
  id: number;
  status: string;
  notes?: string;
  job: Job;
  createdAt: string;
  updatedAt: string;
};

type Dashboard = {
  total: number;
  byStatus: Record<string, number>;
};

type DocumentItem = {
  id: number;
  type: "CV" | "COVER_LETTER";
  status: "DRAFT" | "APPROVED";
  content: string;
  createdAt: string;
  job: Job;
};

type AutomationField = {
  fieldName: string;
  value: string;
  supported: boolean;
};

type AutomationPreview = {
  url: string;
  fields: AutomationField[];
  submissionConfirmed: boolean;
};

type CodeAnalysis = {
  functions: string[];
  classes: string[];
  imports: string[];
  lines: number;
};

const emptyProfile: Profile = {
  fullName: "",
  email: "",
  phone: "",
  professionalTitle: "",
  preferredLocation: "",
  education: "",
  desiredEmploymentType: "FULL_TIME",
  yearsOfExperience: 3,
  skills: [],
};

const emptyJobDraft = {
  title: "",
  company: "",
  location: "",
  employmentType: "Full-time",
  description: "",
  skills: "",
  minimumExperienceYears: 2,
};

async function apiRequest<T>(baseUrl: string, path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${baseUrl}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({ error: "Request failed" }));
    throw new Error(body.error || body.detail || `Request failed with status ${response.status}`);
  }
  return response.status === 204 ? (undefined as T) : response.json();
}

function App() {
  const [activeTab, setActiveTab] = useState<"jobs" | "docs" | "apps" | "automation" | "code" | "profile">("jobs");
  const [profile, setProfile] = useState<Profile>(emptyProfile);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [matches, setMatches] = useState<Record<number, MatchResult>>({});
  const [keyword, setKeyword] = useState("");
  const [jobDraft, setJobDraft] = useState(emptyJobDraft);
  const [showAddJobModal, setShowAddJobModal] = useState(false);
  const [applications, setApplications] = useState<Application[]>([]);
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [editingDocId, setEditingDocId] = useState<number | null>(null);
  const [docContentDraft, setDocContentDraft] = useState("");

  // Automation state
  const [automationUrl, setAutomationUrl] = useState("https://careers.example.com/apply/senior-dev");
  const [automationPreview, setAutomationPreview] = useState<AutomationPreview | null>(null);
  const [confirmedSubmission, setConfirmedSubmission] = useState(false);
  const [seleniumResult, setSeleniumResult] = useState<{
    url: string;
    status: string;
    fieldsFilled: string[];
    executionLogs: string[];
    submitted: boolean;
  } | null>(null);
  const [isSeleniumRunning, setIsSeleniumRunning] = useState(false);
  const [isCollectingJobs, setIsCollectingJobs] = useState(false);

  // AI Code Agent state
  const [pythonSource, setPythonSource] = useState(
    'class Solution:\n    def two_sum(self, nums: list[int], target: int) -> list[int]:\n        seen = {}\n        for i, num in enumerate(nums):\n            diff = target - num\n            if diff in seen:\n                return [seen[diff], i]\n            seen[num] = i\n        return []\n'
  );
  const [codeAnalysis, setCodeAnalysis] = useState<CodeAnalysis | null>(null);
  const [testSource, setTestSource] = useState("");
  const [testExecutionResult, setTestExecutionResult] = useState<{ status: string; exitCode: number; output: string } | null>(null);
  const [isExecutingCode, setIsExecutingCode] = useState(false);

  // Health state
  const [backendHealthy, setBackendHealthy] = useState<boolean | null>(null);
  const [aiHealthy, setAiHealthy] = useState<boolean | null>(null);

  // Toast notifications
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const showNotice = (msg: string) => {
    setMessage(msg);
    setError("");
  };

  const showError = (err: string) => {
    setError(err);
    setMessage("");
  };

  // Check health
  const checkHealth = async () => {
    try {
      await apiRequest<{ status: string }>(API, "/api/health");
      setBackendHealthy(true);
    } catch {
      setBackendHealthy(false);
    }
    try {
      await apiRequest<{ status: string }>(AI_API, "/health");
      setAiHealthy(true);
    } catch {
      setAiHealthy(false);
    }
  };

  // Load jobs & matches
  const loadJobs = async (search = "", currentProfile = profile) => {
    try {
      const jobList = await apiRequest<Job[]>(API, `/api/jobs${search ? `?keyword=${encodeURIComponent(search)}` : ""}`);
      setJobs(jobList);

      if (currentProfile.id && jobList.length > 0) {
        const matchMap: Record<number, MatchResult> = {};
        await Promise.all(
          jobList.map(async (j) => {
            try {
              matchMap[j.id] = await apiRequest<MatchResult>(API, `/api/matching/profiles/${currentProfile.id}/jobs/${j.id}`);
            } catch {
              // ignore individual match errors
            }
          })
        );
        setMatches(matchMap);
      }
    } catch (err) {
      showError(err instanceof Error ? err.message : "Failed to load job offers");
    }
  };

  // Load documents
  const loadDocuments = async (profileId: number) => {
    try {
      const docs = await apiRequest<DocumentItem[]>(API, `/api/documents?profileId=${profileId}`);
      setDocuments(docs);
    } catch {
      // ignore
    }
  };

  // Load applications & dashboard
  const loadApplications = async (profileId: number) => {
    try {
      const [apps, dash] = await Promise.all([
        apiRequest<Application[]>(API, `/api/applications?profileId=${profileId}`),
        apiRequest<Dashboard>(API, `/api/applications/dashboard?profileId=${profileId}`),
      ]);
      setApplications(apps);
      setDashboard(dash);
    } catch {
      // ignore
    }
  };

  // Initial load
  useEffect(() => {
    void checkHealth();
    void apiRequest<Profile[]>(API, "/api/profiles")
      .then(async (profiles) => {
        if (profiles[0]) {
          setProfile(profiles[0]);
          await loadJobs("", profiles[0]);
          await loadDocuments(profiles[0].id!);
          await loadApplications(profiles[0].id!);
        } else {
          await loadJobs("");
        }
      })
      .catch(() => {
        void loadJobs("");
      });
  }, []);

  // Save profile
  const handleSaveProfile = async (e: FormEvent) => {
    e.preventDefault();
    try {
      const saved = profile.id
        ? await apiRequest<Profile>(API, `/api/profiles/${profile.id}`, { method: "PUT", body: JSON.stringify(profile) })
        : await apiRequest<Profile>(API, "/api/profiles", { method: "POST", body: JSON.stringify(profile) });
      setProfile(saved);
      showNotice("Profile successfully updated.");
      await loadJobs(keyword, saved);
      if (saved.id) {
        await loadApplications(saved.id);
        await loadDocuments(saved.id);
      }
    } catch (err) {
      showError(err instanceof Error ? err.message : "Could not save profile");
    }
  };

  // Save job offer
  const handleSaveJob = async (e: FormEvent) => {
    e.preventDefault();
    try {
      await apiRequest<Job>(API, "/api/jobs", {
        method: "POST",
        body: JSON.stringify({
          ...jobDraft,
          skills: jobDraft.skills.split(",").map((s) => s.trim()).filter(Boolean),
        }),
      });
      setJobDraft(emptyJobDraft);
      setShowAddJobModal(false);
      showNotice("Job offer created successfully.");
      await loadJobs(keyword);
    } catch (err) {
      showError(err instanceof Error ? err.message : "Could not save job offer");
    }
  };

  // Delete job offer
  const handleDeleteJob = async (jobId: number) => {
    if (!window.confirm("Are you sure you want to delete this job opportunity?")) return;
    try {
      await apiRequest(API, `/api/jobs/${jobId}`, { method: "DELETE" });
      showNotice("Job opportunity removed.");
      await loadJobs(keyword);
    } catch (err) {
      showError(err instanceof Error ? err.message : "Could not delete job offer");
    }
  };

  // Track application
  const handleCreateApplication = async (jobId: number) => {
    if (!profile.id) {
      showError("Please create and save your profile first.");
      setActiveTab("profile");
      return;
    }
    try {
      await apiRequest<Application>(API, `/api/applications?profileId=${profile.id}&jobId=${jobId}`, { method: "POST" });
      showNotice("Application tracked! Check the Applications board.");
      await loadApplications(profile.id);
    } catch (err) {
      showError(err instanceof Error ? err.message : "Could not track application");
    }
  };

  // Update application status
  const handleUpdateAppStatus = async (appId: number, status: string) => {
    try {
      await apiRequest<Application>(API, `/api/applications/${appId}`, {
        method: "PATCH",
        body: JSON.stringify({ status }),
      });
      showNotice(`Application status updated to ${status}.`);
      if (profile.id) await loadApplications(profile.id);
    } catch (err) {
      showError(err instanceof Error ? err.message : "Could not update status");
    }
  };

  // Generate document
  const handleGenerateDoc = async (jobId: number, type: "CV" | "COVER_LETTER") => {
    if (!profile.id) {
      showError("Please create and save your profile first.");
      setActiveTab("profile");
      return;
    }
    try {
      const doc = await apiRequest<DocumentItem>(
        API,
        `/api/documents/generate?profileId=${profile.id}&jobId=${jobId}&type=${type}`,
        { method: "POST" }
      );
      showNotice(`${type === "CV" ? "CV" : "Cover Letter"} generated as draft. Review it in the Documents Studio.`);
      if (profile.id) await loadDocuments(profile.id);
      setActiveTab("docs");
      setEditingDocId(doc.id);
      setDocContentDraft(doc.content);
    } catch (err) {
      showError(err instanceof Error ? err.message : "Could not generate document");
    }
  };

  // Save document edits
  const handleSaveDocEdit = async (docId: number) => {
    try {
      await apiRequest<DocumentItem>(API, `/api/documents/${docId}`, {
        method: "PUT",
        body: JSON.stringify({ content: docContentDraft }),
      });
      showNotice("Document content saved.");
      setEditingDocId(null);
      if (profile.id) await loadDocuments(profile.id);
    } catch (err) {
      showError(err instanceof Error ? err.message : "Could not update document");
    }
  };

  // Approve document
  const handleApproveDoc = async (docId: number) => {
    try {
      await apiRequest<DocumentItem>(API, `/api/documents/${docId}/approve`, { method: "POST" });
      showNotice("Document approved and finalized!");
      if (profile.id) await loadDocuments(profile.id);
    } catch (err) {
      showError(err instanceof Error ? err.message : "Could not approve document");
    }
  };

  // Automation preview
  const handlePreviewAutomation = async () => {
    if (!profile.id) {
      showError("Please save your profile before previewing automation.");
      setActiveTab("profile");
      return;
    }
    try {
      const preview = await apiRequest<AutomationPreview>(
        API,
        `/api/automation/preview?profileId=${profile.id}&url=${encodeURIComponent(automationUrl)}`,
        { method: "POST" }
      );
      setAutomationPreview(preview);
      setConfirmedSubmission(false);
      showNotice("Form fields analyzed. Review mapped values before submitting.");
    } catch (err) {
      showError(err instanceof Error ? err.message : "Automation preview failed");
    }
  };

  // Auto-collect matching job opportunities (PBI & Proxym requirements)
  const handleCollectMatchingJobs = async () => {
    if (!profile.id) {
      showError("Please create and save your profile first to discover matching jobs.");
      setActiveTab("profile");
      return;
    }
    setIsCollectingJobs(true);
    try {
      const res = await apiRequest<{ totalFound: number; newlyAdded: number }>(
        API,
        `/api/jobs/collect-matching?profileId=${profile.id}`,
        { method: "POST" }
      );
      showNotice(`Discovered and collected ${res.totalFound} matching opportunities (${res.newlyAdded} new added to your board)!`);
      await loadJobs(keyword, profile);
    } catch (err) {
      showError(err instanceof Error ? err.message : "Failed to auto-collect matching jobs");
    } finally {
      setIsCollectingJobs(false);
    }
  };

  // Selenium Automation runner
  const handleRunSelenium = async (confirm = false) => {
    if (!profile.id) {
      showError("Please save your profile before launching Selenium browser automation.");
      setActiveTab("profile");
      return;
    }
    setIsSeleniumRunning(true);
    try {
      const res = await apiRequest<{
        url: string;
        status: string;
        fieldsFilled: string[];
        executionLogs: string[];
        submitted: boolean;
      }>(
        API,
        `/api/automation/selenium-apply?profileId=${profile.id}&url=${encodeURIComponent(automationUrl)}&confirm=${confirm}`,
        { method: "POST" }
      );
      setSeleniumResult(res);
      showNotice(confirm ? "Selenium automated application submission completed!" : "Selenium automated form pre-fill preview finished.");
    } catch (err) {
      showError(err instanceof Error ? err.message : "Selenium browser automation failed");
    } finally {
      setIsSeleniumRunning(false);
    }
  };

  // Automation submit
  const handleSubmitAutomation = async () => {
    if (!automationPreview) return;
    if (!confirmedSubmission) {
      showError("Submission requires explicit user confirmation toggle.");
      return;
    }
    try {
      await apiRequest<AutomationPreview>(API, "/api/automation/submit", {
        method: "POST",
        body: JSON.stringify({ ...automationPreview, submissionConfirmed: true }),
      });
      showNotice("Application payload confirmed and safely submitted!");
    } catch (err) {
      showError(err instanceof Error ? err.message : "Submission failed");
    }
  };

  // AI Code Agent: Analyze
  const handleAnalyzeCode = async () => {
    try {
      const res = await apiRequest<CodeAnalysis>(AI_API, "/api/code/analyze", {
        method: "POST",
        body: JSON.stringify({ source: pythonSource }),
      });
      setCodeAnalysis(res);
      showNotice("AST syntax and structure analysis completed.");
    } catch (err) {
      showError(err instanceof Error ? err.message : "Code analysis failed");
    }
  };

  // AI Code Agent: Generate Tests
  const handleGenerateTests = async () => {
    try {
      const res = await apiRequest<{ analysis: CodeAnalysis; testSource: string }>(AI_API, "/api/code/generate-tests", {
        method: "POST",
        body: JSON.stringify({ source: pythonSource }),
      });
      setCodeAnalysis(res.analysis);
      setTestSource(res.testSource);
      showNotice("Baseline pytest suite generated.");
    } catch (err) {
      showError(err instanceof Error ? err.message : "Test generation failed");
    }
  };

  // AI Code Agent: Execute Tests
  const handleExecuteTests = async () => {
    if (!testSource) {
      showError("Please generate or provide test code first.");
      return;
    }
    setIsExecutingCode(true);
    try {
      const res = await apiRequest<{ status: string; exitCode: number; output: string }>(
        AI_API,
        "/api/code/execute-tests",
        {
          method: "POST",
          body: JSON.stringify({ test_source: testSource }),
        }
      );
      setTestExecutionResult(res);
      showNotice(`Tests finished with result: ${res.status}`);
    } catch (err) {
      showError(err instanceof Error ? err.message : "Test execution failed");
    } finally {
      setIsExecutingCode(false);
    }
  };

  return (
    <div className="app-container">
      {/* Header */}
      <header className="app-header">
        <div className="brand">
          <div className="brand-icon">⚡</div>
          <div>
            <h1 className="brand-title">Smart Job Assistant</h1>
            <p className="brand-subtitle">AI-Powered Job Application, Document Generator & Code Prep</p>
          </div>
        </div>

        <div className="status-pills">
          <span className={`service-pill ${backendHealthy ? "up" : ""}`} title="Backend API on 8080">
            <span className="pulse-dot"></span> Backend {backendHealthy ? "Online" : "Connecting..."}
          </span>
          <span className={`service-pill ${aiHealthy ? "up" : ""}`} title="AI Service on 8000">
            <span className="pulse-dot"></span> AI Service {aiHealthy ? "Online" : "Connecting..."}
          </span>
          {profile.fullName && (
            <span className="service-pill" style={{ color: "#c084fc", borderColor: "rgba(192, 132, 252, 0.3)" }}>
              👤 {profile.fullName}
            </span>
          )}
        </div>
      </header>

      {/* Notifications */}
      {message && (
        <div className="notice-toast success" role="alert">
          <span>✅ {message}</span>
          <button className="close-toast-btn" onClick={() => setMessage("")}>×</button>
        </div>
      )}
      {error && (
        <div className="notice-toast error" role="alert">
          <span>⚠️ {error}</span>
          <button className="close-toast-btn" onClick={() => setError("")}>×</button>
        </div>
      )}

      {/* Navigation Tabs */}
      <nav className="nav-tabs" aria-label="Main Navigation">
        <button
          id="tab-jobs"
          className={`tab-btn ${activeTab === "jobs" ? "active" : ""}`}
          onClick={() => setActiveTab("jobs")}
        >
          💼 Opportunities <span className="tab-badge">{jobs.length}</span>
        </button>
        <button
          id="tab-docs"
          className={`tab-btn ${activeTab === "docs" ? "active" : ""}`}
          onClick={() => setActiveTab("docs")}
        >
          📄 Documents Studio <span className="tab-badge">{documents.length}</span>
        </button>
        <button
          id="tab-apps"
          className={`tab-btn ${activeTab === "apps" ? "active" : ""}`}
          onClick={() => setActiveTab("apps")}
        >
          📊 Applications Board <span className="tab-badge">{applications.length}</span>
        </button>
        <button
          id="tab-automation"
          className={`tab-btn ${activeTab === "automation" ? "active" : ""}`}
          onClick={() => setActiveTab("automation")}
        >
          🤖 Form Automation
        </button>
        <button
          id="tab-code"
          className={`tab-btn ${activeTab === "code" ? "active" : ""}`}
          onClick={() => setActiveTab("code")}
        >
          ⚡ AI Code Studio
        </button>
        <button
          id="tab-profile"
          className={`tab-btn ${activeTab === "profile" ? "active" : ""}`}
          onClick={() => setActiveTab("profile")}
        >
          👤 My Profile
        </button>
      </nav>

      {/* TAB: JOB OPPORTUNITIES */}
      {activeTab === "jobs" && (
        <div>
          <div className="card" style={{ marginBottom: "1.5rem" }}>
            <div className="card-title-row">
              <div>
                <h2 className="card-title">Job Opportunities & Skill Matching</h2>
                <p className="card-desc">Search roles and see real-time skill overlap scores tailored to your profile.</p>
              </div>
              <div style={{ display: "flex", gap: "0.5rem" }}>
                <button
                  id="btn-auto-collect-jobs"
                  className="btn btn-secondary"
                  disabled={isCollectingJobs}
                  onClick={() => void handleCollectMatchingJobs()}
                  title="Automatically search and collect job opportunities matching your profile"
                >
                  {isCollectingJobs ? "Collecting..." : "⚡ Auto-Collect Matching Jobs"}
                </button>
                <button
                  id="btn-add-job-toggle"
                  className="btn btn-primary"
                  onClick={() => setShowAddJobModal(!showAddJobModal)}
                >
                  {showAddJobModal ? "✕ Close Form" : "+ Add Job Opportunity"}
                </button>
              </div>
            </div>

            {/* Add Job Form */}
            {showAddJobModal && (
              <form onSubmit={handleSaveJob} style={{ marginBottom: "2rem", padding: "1.25rem", background: "rgba(0,0,0,0.3)", borderRadius: "var(--radius-md)" }}>
                <h3 style={{ fontSize: "1.05rem", marginBottom: "1rem", color: "#a5b4fc" }}>New Job Opportunity</h3>
                <div className="form-row">
                  <div className="form-group">
                    <label>Job Title *</label>
                    <input
                      required
                      placeholder="e.g. Senior Backend Engineer"
                      value={jobDraft.title}
                      onChange={(e) => setJobDraft({ ...jobDraft, title: e.target.value })}
                    />
                  </div>
                  <div className="form-group">
                    <label>Company *</label>
                    <input
                      required
                      placeholder="e.g. TechCorp Solutions"
                      value={jobDraft.company}
                      onChange={(e) => setJobDraft({ ...jobDraft, company: e.target.value })}
                    />
                  </div>
                </div>
                <div className="form-row">
                  <div className="form-group">
                    <label>Location</label>
                    <input
                      placeholder="e.g. Remote / New York, NY"
                      value={jobDraft.location}
                      onChange={(e) => setJobDraft({ ...jobDraft, location: e.target.value })}
                    />
                  </div>
                  <div className="form-group">
                    <label>Employment Type</label>
                    <input
                      placeholder="e.g. Full-time"
                      value={jobDraft.employmentType}
                      onChange={(e) => setJobDraft({ ...jobDraft, employmentType: e.target.value })}
                    />
                  </div>
                </div>
                <div className="form-group">
                  <label>Required Skills <span className="label-hint">(comma separated)</span></label>
                  <input
                    placeholder="e.g. Java, Spring Boot, PostgreSQL, Docker"
                    value={jobDraft.skills}
                    onChange={(e) => setJobDraft({ ...jobDraft, skills: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label>Role Description</label>
                  <textarea
                    placeholder="Paste job description..."
                    value={jobDraft.description}
                    onChange={(e) => setJobDraft({ ...jobDraft, description: e.target.value })}
                  />
                </div>
                <button type="submit" className="btn btn-success">Save Job Opportunity</button>
              </form>
            )}

            {/* Search Bar */}
            <form
              className="search-bar-row"
              onSubmit={(e) => {
                e.preventDefault();
                void loadJobs(keyword);
              }}
            >
              <input
                id="input-search-jobs"
                placeholder="Search by title, company, or keywords..."
                value={keyword}
                onChange={(e) => setKeyword(e.target.value)}
              />
              <button type="submit" className="btn btn-secondary">Search</button>
              {keyword && (
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => {
                    setKeyword("");
                    void loadJobs("");
                  }}
                >
                  Clear
                </button>
              )}
            </form>

            {/* Job List */}
            <div>
              {jobs.length === 0 ? (
                <p style={{ color: "var(--text-muted)", padding: "2rem", textAlign: "center" }}>
                  No job offers found. Add a new opportunity to calculate skill fit!
                </p>
              ) : (
                jobs.map((job) => {
                  const match = matches[job.id];
                  const scoreClass =
                    match && match.score >= 70 ? "score-high" : match && match.score >= 40 ? "score-mid" : "score-low";

                  return (
                    <article className="job-item" key={job.id}>
                      <div className="job-header">
                        <div>
                          <h3 className="job-role">{job.title}</h3>
                          <p className="job-meta">
                            {job.company} · {job.location || "Remote / Unspecified"}
                            {job.employmentType ? ` · ${job.employmentType}` : ""}
                          </p>
                        </div>
                        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                          {match ? (
                            <span className={`match-score-badge ${scoreClass}`} title="Skill match score">
                              🎯 {match.score}% Fit
                            </span>
                          ) : (
                            <span className="status-pill status-SAVED">{job.status}</span>
                          )}
                        </div>
                      </div>

                      {job.description && (
                        <p style={{ fontSize: "0.85rem", color: "var(--text-muted)", margin: "0.5rem 0 0.8rem", whiteSpace: "pre-line" }}>
                          {job.description.length > 250 ? `${job.description.slice(0, 250)}...` : job.description}
                        </p>
                      )}

                      {/* Match Analysis Breakdown */}
                      {match && (
                        <div className="match-details">
                          <p className="match-recommendation">{match.recommendation}</p>
                          <div style={{ display: "flex", flexWrap: "wrap", gap: "1rem" }}>
                            {match.matchingSkills.length > 0 && (
                              <div>
                                <span style={{ color: "#34d399", fontSize: "0.75rem", fontWeight: 700 }}>MATCHING SKILLS:</span>
                                <div className="skill-pills-row">
                                  {match.matchingSkills.map((s) => (
                                    <span key={s} className="skill-pill matching">✓ {s}</span>
                                  ))}
                                </div>
                              </div>
                            )}
                            {match.missingSkills.length > 0 && (
                              <div>
                                <span style={{ color: "#f87171", fontSize: "0.75rem", fontWeight: 700 }}>SKILLS TO ACQUIRE:</span>
                                <div className="skill-pills-row">
                                  {match.missingSkills.map((s) => (
                                    <span key={s} className="skill-pill missing">✕ {s}</span>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                        </div>
                      )}

                      {/* Required Skills Row */}
                      {!match && job.skills.length > 0 && (
                        <div className="skill-pills-row" style={{ margin: "0.5rem 0" }}>
                          {job.skills.map((s) => (
                            <span key={s} className="skill-pill">{s}</span>
                          ))}
                        </div>
                      )}

                      {/* Job Actions */}
                      <div className="job-actions-toolbar">
                        <button
                          type="button"
                          className="btn btn-primary btn-sm"
                          onClick={() => void handleCreateApplication(job.id)}
                        >
                          📌 Track Application
                        </button>
                        <button
                          type="button"
                          className="btn btn-secondary btn-sm"
                          onClick={() => void handleGenerateDoc(job.id, "CV")}
                        >
                          📄 Generate CV Draft
                        </button>
                        <button
                          type="button"
                          className="btn btn-secondary btn-sm"
                          onClick={() => void handleGenerateDoc(job.id, "COVER_LETTER")}
                        >
                          ✉️ Generate Cover Letter
                        </button>
                        <button
                          type="button"
                          className="btn btn-secondary btn-sm"
                          style={{ marginLeft: "auto", color: "#f87171" }}
                          onClick={() => void handleDeleteJob(job.id)}
                        >
                          🗑 Delete
                        </button>
                      </div>
                    </article>
                  );
                })
              )}
            </div>
          </div>
        </div>
      )}

      {/* TAB: DOCUMENTS STUDIO */}
      {activeTab === "docs" && (
        <div className="card">
          <div className="card-title-row">
            <div>
              <h2 className="card-title">Application Documents Studio</h2>
              <p className="card-desc">
                Review, customize, and approve your tailored CVs and cover letters. All generated documents begin as DRAFT.
              </p>
            </div>
          </div>

          {documents.length === 0 ? (
            <p style={{ color: "var(--text-muted)", padding: "2rem", textAlign: "center" }}>
              No documents generated yet. Visit the Opportunities tab and click "Generate CV" or "Generate Cover Letter"!
            </p>
          ) : (
            <div style={{ display: "grid", gap: "1.5rem" }}>
              {documents.map((doc) => {
                const isEditing = editingDocId === doc.id;
                return (
                  <article
                    key={doc.id}
                    style={{
                      border: "1px solid var(--border-subtle)",
                      borderRadius: "var(--radius-md)",
                      padding: "1.25rem",
                      background: "rgba(0,0,0,0.2)",
                    }}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.85rem" }}>
                      <div>
                        <span style={{ fontWeight: 800, fontSize: "1.05rem", color: "#fff", marginRight: "0.75rem" }}>
                          {doc.type === "CV" ? "Curriculum Vitae (CV)" : "Cover Letter"}
                        </span>
                        <span style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>
                          for {doc.job.title} at {doc.job.company}
                        </span>
                      </div>
                      <span className={`status-pill status-${doc.status}`}>{doc.status}</span>
                    </div>

                    {isEditing ? (
                      <div>
                        <textarea
                          style={{ minHeight: "180px", fontFamily: "var(--font-mono)", fontSize: "0.85rem" }}
                          value={docContentDraft}
                          onChange={(e) => setDocContentDraft(e.target.value)}
                        />
                        <div style={{ display: "flex", gap: "0.5rem", marginTop: "0.75rem" }}>
                          <button className="btn btn-success btn-sm" onClick={() => void handleSaveDocEdit(doc.id)}>
                            💾 Save Changes
                          </button>
                          <button className="btn btn-secondary btn-sm" onClick={() => setEditingDocId(null)}>
                            Cancel
                          </button>
                        </div>
                      </div>
                    ) : (
                      <div>
                        <pre
                          style={{
                            background: "rgba(0,0,0,0.4)",
                            padding: "1rem",
                            borderRadius: "var(--radius-sm)",
                            fontFamily: "var(--font-sans)",
                            fontSize: "0.88rem",
                            lineHeight: 1.6,
                            whiteSpace: "pre-wrap",
                            color: "#cbd5e1",
                            maxHeight: "260px",
                            overflowY: "auto",
                          }}
                        >
                          {doc.content}
                        </pre>
                        <div style={{ display: "flex", gap: "0.5rem", marginTop: "0.85rem" }}>
                          <button
                            className="btn btn-secondary btn-sm"
                            onClick={() => {
                              setEditingDocId(doc.id);
                              setDocContentDraft(doc.content);
                            }}
                          >
                            ✏️ Edit Draft
                          </button>
                          {doc.status !== "APPROVED" && (
                            <button
                              className="btn btn-success btn-sm"
                              onClick={() => void handleApproveDoc(doc.id)}
                            >
                              ✓ Approve Document
                            </button>
                          )}
                          <button
                            className="btn btn-secondary btn-sm"
                            onClick={() => {
                              void navigator.clipboard.writeText(doc.content);
                              showNotice("Document text copied to clipboard!");
                            }}
                          >
                            📋 Copy Text
                          </button>
                        </div>
                      </div>
                    )}
                  </article>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* TAB: APPLICATIONS BOARD */}
      {activeTab === "apps" && (
        <div className="card">
          <h2 className="card-title">Tracked Applications Board</h2>
          <p className="card-desc">Monitor pipeline stages from Draft to Offer and record private follow-up notes.</p>

          {/* Metrics */}
          <div className="metrics-row">
            <div className="metric-box">
              <div className="metric-val">{dashboard?.total ?? applications.length}</div>
              <div className="metric-label">TOTAL APPLICATIONS</div>
            </div>
            {dashboard &&
              Object.entries(dashboard.byStatus).map(([st, count]) => (
                <div className="metric-box" key={st}>
                  <div className="metric-val" style={{ fontSize: "1.8rem" }}>{count}</div>
                  <div className="metric-label">{st}</div>
                </div>
              ))}
          </div>

          {/* Table */}
          {applications.length === 0 ? (
            <p style={{ color: "var(--text-muted)", padding: "2rem", textAlign: "center" }}>
              No applications tracked yet. Click "Track Application" on any job opportunity.
            </p>
          ) : (
            <div style={{ overflowX: "auto" }}>
              <table className="list-table">
                <thead>
                  <tr>
                    <th>Role & Company</th>
                    <th>Status</th>
                    <th>Update Stage</th>
                    <th>Notes</th>
                  </tr>
                </thead>
                <tbody>
                  {applications.map((app) => (
                    <tr key={app.id}>
                      <td>
                        <strong style={{ color: "#fff" }}>{app.job.title}</strong>
                        <div style={{ color: "var(--text-muted)", fontSize: "0.8rem" }}>
                          {app.job.company} · {app.job.location || "Remote"}
                        </div>
                      </td>
                      <td>
                        <span className={`status-pill status-${app.status}`}>{app.status}</span>
                      </td>
                      <td>
                        <select
                          value={app.status}
                          onChange={(e) => void handleUpdateAppStatus(app.id, e.target.value)}
                          style={{ width: "auto", padding: "0.4rem 0.6rem", fontSize: "0.82rem" }}
                        >
                          <option value="DRAFT">DRAFT</option>
                          <option value="APPLIED">APPLIED</option>
                          <option value="INTERVIEWING">INTERVIEWING</option>
                          <option value="OFFERED">OFFERED</option>
                          <option value="REJECTED">REJECTED</option>
                        </select>
                      </td>
                      <td>
                        <span style={{ color: "var(--text-muted)", fontSize: "0.82rem" }}>
                          {app.notes || "No notes"}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* TAB: FORM AUTOMATION */}
      {activeTab === "automation" && (
        <div className="card">
          <h2 className="card-title">Selenium Form Automation & Pre-fill (PRX-2026-01)</h2>
          <p className="card-desc">
            Using Selenium WebDriver, the assistant automatically navigates to external job portals, maps your candidate profile
            to web form inputs (Name, Email, Phone, Cover Letter), and securely submits on your behalf.
          </p>

          <div className="form-group">
            <label>Target Application Form URL</label>
            <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap" }}>
              <input
                id="input-automation-url"
                value={automationUrl}
                onChange={(e) => setAutomationUrl(e.target.value)}
                placeholder="https://..."
                style={{ flex: 1, minWidth: "280px" }}
              />
              <button className="btn btn-secondary" onClick={() => void handlePreviewAutomation()}>
                🔍 Inspect Form Fields
              </button>
              <button
                className="btn btn-primary"
                disabled={isSeleniumRunning}
                onClick={() => void handleRunSelenium(false)}
              >
                {isSeleniumRunning ? "Selenium Running..." : "🤖 Selenium Fill Form (Preview)"}
              </button>
              <button
                className="btn btn-success"
                disabled={isSeleniumRunning}
                onClick={() => void handleRunSelenium(true)}
              >
                {isSeleniumRunning ? "Submitting..." : "🚀 Selenium Fill & Submit"}
              </button>
            </div>
          </div>

          {/* Selenium Live Execution Results & Logs */}
          {seleniumResult && (
            <div style={{ marginTop: "1.5rem" }}>
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  padding: "0.85rem 1.25rem",
                  borderRadius: "var(--radius-sm)",
                  background: seleniumResult.submitted ? "var(--color-success-bg)" : "var(--color-info-bg)",
                  border: `1px solid ${seleniumResult.submitted ? "rgba(16, 185, 129, 0.4)" : "rgba(6, 182, 212, 0.4)"}`,
                  marginBottom: "1rem",
                }}
              >
                <div>
                  <strong style={{ color: "#fff", marginRight: "0.5rem" }}>Selenium Automation:</strong>
                  <span style={{ color: seleniumResult.submitted ? "#34d399" : "#38bdf8" }}>
                    {seleniumResult.submitted ? "Application Submitted Successfully!" : "Form Fields Pre-Filled (Preview Mode)"}
                  </span>
                </div>
                <span className="status-pill status-APPROVED">{seleniumResult.status}</span>
              </div>

              <div style={{ marginBottom: "1rem" }}>
                <span style={{ fontSize: "0.82rem", fontWeight: 700, color: "var(--text-muted)" }}>FIELDS FILLED BY SELENIUM:</span>
                <div className="skill-pills-row" style={{ marginTop: "0.4rem" }}>
                  {seleniumResult.fieldsFilled.map((field) => (
                    <span key={field} className="skill-pill matching">✓ {field}</span>
                  ))}
                </div>
              </div>

              <div className="terminal-window">
                <div className="terminal-header">
                  <span>Selenium WebDriver Execution Console</span>
                  <span style={{ marginLeft: "auto", color: "#38bdf8" }}>{seleniumResult.url}</span>
                </div>
                <div className="terminal-body">
                  {seleniumResult.executionLogs.map((log, i) => (
                    <div key={i} style={{ marginBottom: "0.25rem" }}>
                      <span style={{ color: "var(--text-dim)", marginRight: "0.5rem" }}>[{i + 1}]</span>
                      {log}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {automationPreview && !seleniumResult && (
            <div style={{ marginTop: "1.5rem", background: "rgba(0,0,0,0.3)", padding: "1.25rem", borderRadius: "var(--radius-md)" }}>
              <h3 style={{ fontSize: "1rem", color: "#a5b4fc", marginBottom: "0.75rem" }}>
                Target URL: <span style={{ color: "var(--text-muted)", fontWeight: 400 }}>{automationPreview.url}</span>
              </h3>

              <div style={{ display: "grid", gap: "0.6rem", marginBottom: "1.25rem" }}>
                {automationPreview.fields.map((f) => (
                  <div
                    key={f.fieldName}
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                      padding: "0.65rem 0.9rem",
                      borderRadius: "var(--radius-sm)",
                      background: f.supported ? "rgba(16, 185, 129, 0.1)" : "rgba(239, 68, 68, 0.1)",
                      border: `1px solid ${f.supported ? "rgba(16, 185, 129, 0.3)" : "rgba(239, 68, 68, 0.3)"}`,
                    }}
                  >
                    <div>
                      <strong style={{ color: "#fff", marginRight: "0.5rem" }}>{f.fieldName}:</strong>
                      <span style={{ color: "var(--text-muted)" }}>{f.value || "<empty>"}</span>
                    </div>
                    <span style={{ fontSize: "0.75rem", fontWeight: 700, color: f.supported ? "#34d399" : "#f87171" }}>
                      {f.supported ? "SUPPORTED" : "MANUAL REVIEW REQUIRED"}
                    </span>
                  </div>
                ))}
              </div>

              <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginBottom: "1rem" }}>
                <input
                  type="checkbox"
                  id="confirm-submit-checkbox"
                  style={{ width: "auto" }}
                  checked={confirmedSubmission}
                  onChange={(e) => setConfirmedSubmission(e.target.checked)}
                />
                <label htmlFor="confirm-submit-checkbox" style={{ margin: 0, cursor: "pointer", color: "#fff" }}>
                  I have reviewed all pre-filled and manual fields and authorize submission.
                </label>
              </div>

              <button
                className="btn btn-success"
                disabled={!confirmedSubmission}
                onClick={() => void handleSubmitAutomation()}
                style={{ opacity: confirmedSubmission ? 1 : 0.5, cursor: confirmedSubmission ? "pointer" : "not-allowed" }}
              >
                🚀 Confirm & Submit Safe Application
              </button>
            </div>
          )}
        </div>
      )}

      {/* TAB: AI CODE STUDIO */}
      {activeTab === "code" && (
        <div className="card">
          <h2 className="card-title">AI Code & Test Studio (PBI-09)</h2>
          <p className="card-desc">
            Local AST static analysis, automated pytest baseline test generation, and isolated execution with timeout protections.
          </p>

          <div className="form-group">
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.4rem" }}>
              <label>Python Solution Source Code</label>
              <button
                type="button"
                className="btn btn-secondary btn-sm"
                onClick={() =>
                  setPythonSource(
                    'def binary_search(arr: list[int], target: int) -> int:\n    left, right = 0, len(arr) - 1\n    while left <= right:\n        mid = (left + right) // 2\n        if arr[mid] == target:\n            return mid\n        elif arr[mid] < target:\n            left = mid + 1\n        else:\n            right = mid - 1\n    return -1\n'
                  )
                }
              >
                Load Binary Search Example
              </button>
            </div>
            <textarea
              className="code-editor"
              value={pythonSource}
              onChange={(e) => setPythonSource(e.target.value)}
            />
          </div>

          <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap", marginBottom: "1.5rem" }}>
            <button className="btn btn-primary" onClick={() => void handleAnalyzeCode()}>
              🔍 Run AST Analysis
            </button>
            <button className="btn btn-secondary" onClick={() => void handleGenerateTests()}>
              ⚡ Generate pytest Baseline
            </button>
          </div>

          {/* AST Analysis Result */}
          {codeAnalysis && (
            <div style={{ background: "rgba(0,0,0,0.3)", padding: "1.25rem", borderRadius: "var(--radius-md)", marginBottom: "1.5rem" }}>
              <h3 style={{ fontSize: "1rem", color: "#38bdf8", marginBottom: "0.75rem" }}>AST Structural Analysis</h3>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))", gap: "1rem" }}>
                <div className="metric-box">
                  <div className="metric-val" style={{ fontSize: "1.8rem" }}>{codeAnalysis.lines}</div>
                  <div className="metric-label">LINES OF CODE</div>
                </div>
                <div className="metric-box">
                  <div className="metric-val" style={{ fontSize: "1.8rem" }}>{codeAnalysis.functions.length}</div>
                  <div className="metric-label">FUNCTIONS ({codeAnalysis.functions.join(", ") || "none"})</div>
                </div>
                <div className="metric-box">
                  <div className="metric-val" style={{ fontSize: "1.8rem" }}>{codeAnalysis.classes.length}</div>
                  <div className="metric-label">CLASSES ({codeAnalysis.classes.join(", ") || "none"})</div>
                </div>
                <div className="metric-box">
                  <div className="metric-val" style={{ fontSize: "1.8rem" }}>{codeAnalysis.imports.length}</div>
                  <div className="metric-label">IMPORTS ({codeAnalysis.imports.join(", ") || "none"})</div>
                </div>
              </div>
            </div>
          )}

          {/* Generated Tests Section */}
          {testSource && (
            <div style={{ marginTop: "1.5rem" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.5rem" }}>
                <label style={{ margin: 0 }}>Generated pytest Test Suite</label>
                <button
                  className="btn btn-success btn-sm"
                  disabled={isExecutingCode}
                  onClick={() => void handleExecuteTests()}
                >
                  {isExecutingCode ? "Running Tests..." : "▶ Execute Tests Now"}
                </button>
              </div>
              <textarea
                className="code-editor"
                style={{ color: "#a5f3fc" }}
                value={testSource}
                onChange={(e) => setTestSource(e.target.value)}
              />
            </div>
          )}

          {/* Test Execution Output */}
          {testExecutionResult && (
            <div className="terminal-window">
              <div className="terminal-header">
                <span>pytest output</span>
                <span style={{ marginLeft: "auto", fontWeight: 700, color: testExecutionResult.status === "OK" ? "#34d399" : "#f87171" }}>
                  STATUS: {testExecutionResult.status} (exit code: {testExecutionResult.exitCode})
                </span>
              </div>
              <div className="terminal-body">{testExecutionResult.output}</div>
            </div>
          )}
        </div>
      )}

      {/* TAB: PROFILE */}
      {activeTab === "profile" && (
        <div className="card">
          <h2 className="card-title">Professional Profile</h2>
          <p className="card-desc">Configure your personal, contact, and skillset data for matching and automated documents.</p>

          <form onSubmit={handleSaveProfile}>
            <div className="form-row">
              <div className="form-group">
                <label>Full Name *</label>
                <input
                  required
                  placeholder="e.g. Alex Morgan"
                  value={profile.fullName}
                  onChange={(e) => setProfile({ ...profile, fullName: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label>Email Address *</label>
                <input
                  required
                  type="email"
                  placeholder="e.g. alex@example.com"
                  value={profile.email}
                  onChange={(e) => setProfile({ ...profile, email: e.target.value })}
                />
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>Phone Number</label>
                <input
                  placeholder="e.g. +1 (555) 019-2834"
                  value={profile.phone || ""}
                  onChange={(e) => setProfile({ ...profile, phone: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label>Professional Title</label>
                <input
                  placeholder="e.g. Senior Full-Stack Engineer"
                  value={profile.professionalTitle || ""}
                  onChange={(e) => setProfile({ ...profile, professionalTitle: e.target.value })}
                />
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>Preferred Location</label>
                <input
                  placeholder="e.g. Remote / San Francisco, CA"
                  value={profile.preferredLocation || ""}
                  onChange={(e) => setProfile({ ...profile, preferredLocation: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label>Years of Experience</label>
                <input
                  type="number"
                  min="0"
                  max="50"
                  value={profile.yearsOfExperience ?? 0}
                  onChange={(e) => setProfile({ ...profile, yearsOfExperience: parseInt(e.target.value, 10) || 0 })}
                />
              </div>
            </div>

            <div className="form-group">
              <label>Education & Degrees</label>
              <input
                placeholder="e.g. B.S. Computer Science, Stanford University"
                value={profile.education || ""}
                onChange={(e) => setProfile({ ...profile, education: e.target.value })}
              />
            </div>

            <div className="form-group">
              <label>Technical Skills <span className="label-hint">(comma separated)</span></label>
              <input
                placeholder="e.g. Python, Java, React, TypeScript, Docker, SQL, AWS"
                value={profile.skills.join(", ")}
                onChange={(e) =>
                  setProfile({
                    ...profile,
                    skills: e.target.value.split(",").map((s) => s.trim()).filter(Boolean),
                  })
                }
              />
              <div className="skill-pills-row" style={{ marginTop: "0.6rem" }}>
                {profile.skills.map((skill) => (
                  <span key={skill} className="skill-pill matching">{skill}</span>
                ))}
              </div>
            </div>

            <button type="submit" className="btn btn-primary">Save Profile Details</button>
          </form>
        </div>
      )}
    </div>
  );
}

createRoot(document.getElementById("root")!).render(<App />);
