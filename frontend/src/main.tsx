import { FormEvent, useEffect, useState } from "react";
import { createRoot } from "react-dom/client";

import "./styles.css";

const API = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8080";

type Profile = {
  id?: number;
  fullName: string;
  email: string;
  professionalTitle: string;
  preferredLocation: string;
  skills: string[];
};

type Job = {
  id: number;
  title: string;
  company: string;
  location: string;
  description: string;
  skills: string[];
  status: string;
};

type Application = {
  id: number;
  status: string;
  job: Job;
};

type Dashboard = {
  total: number;
  byStatus: Record<string, number>;
};

type JobDraft = {
  title: string;
  company: string;
  location: string;
  description: string;
  skills: string;
};

const emptyProfile: Profile = {
  fullName: "",
  email: "",
  professionalTitle: "",
  preferredLocation: "",
  skills: [],
};

const emptyJob: JobDraft = { title: "", company: "", location: "", description: "", skills: "" };

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({ error: "Request failed" }));
    throw new Error(body.error ?? "Request failed");
  }
  return response.status === 204 ? (undefined as T) : response.json();
}

function App() {
  const [profile, setProfile] = useState<Profile>(emptyProfile);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [keyword, setKeyword] = useState("");
  const [jobDraft, setJobDraft] = useState<JobDraft>(emptyJob);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [applications, setApplications] = useState<Application[]>([]);
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);

  const loadJobs = async (search = "") => {
    try {
      setJobs(await request<Job[]>(`/api/jobs${search ? `?keyword=${encodeURIComponent(search)}` : ""}`));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not load jobs");
    }
  };

  useEffect(() => {
    void loadJobs();
    void request<Profile[]>("/api/profiles").then((profiles) => {
      if (profiles[0]) {
        setProfile(profiles[0]);
        void request<Application[]>(`/api/applications?profileId=${profiles[0].id}`).then(setApplications).catch(() => undefined);
        void request<Dashboard>(`/api/applications/dashboard?profileId=${profiles[0].id}`).then(setDashboard).catch(() => undefined);
      }
    }).catch(() => undefined);
  }, []);

  const saveProfile = async (event: FormEvent) => {
    event.preventDefault();
    setError("");
    try {
      const payload = { ...profile, skills: profile.skills };
      const saved = profile.id
        ? await request<Profile>(`/api/profiles/${profile.id}`, { method: "PUT", body: JSON.stringify(payload) })
        : await request<Profile>("/api/profiles", { method: "POST", body: JSON.stringify(payload) });
      setProfile(saved);
      setMessage("Profile saved.");
      void request<Dashboard>(`/api/applications/dashboard?profileId=${saved.id}`).then(setDashboard).catch(() => undefined);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not save profile");
    }
  };

  const createApplication = async (jobId: number) => {
    if (!profile.id) {
      setError("Save your profile before creating an application.");
      return;
    }
    try {
      const application = await request<Application>(`/api/applications?profileId=${profile.id}&jobId=${jobId}`, { method: "POST" });
      setApplications([...applications, application]);
      setDashboard(await request<Dashboard>(`/api/applications/dashboard?profileId=${profile.id}`));
      setMessage("Application created as draft.");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not create application");
    }
  };

  const generateDocument = async (jobId: number, type: "CV" | "COVER_LETTER") => {
    if (!profile.id) {
      setError("Save your profile before generating documents.");
      return;
    }
    try {
      await request(`/api/documents/generate?profileId=${profile.id}&jobId=${jobId}&type=${type}`, { method: "POST" });
      setMessage(`${type === "CV" ? "CV" : "Cover letter"} draft generated. Review and approve it before use.`);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not generate document");
    }
  };

  const updateSkills = (value: string) => {
    setProfile({ ...profile, skills: value.split(",").map((skill) => skill.trim()).filter(Boolean) });
  };

  const saveJob = async (event: FormEvent) => {
    event.preventDefault();
    setError("");
    try {
      await request<Job>("/api/jobs", {
        method: "POST",
        body: JSON.stringify({
          ...jobDraft,
          skills: jobDraft.skills.split(",").map((skill) => skill.trim()).filter(Boolean),
        }),
      });
      setJobDraft(emptyJob);
      setMessage("Job offer saved.");
      await loadJobs(keyword);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not save job offer");
    }
  };

  return (
    <main className="app">
      <header>
        <p className="eyebrow">Smart Job Application Assistant</p>
        <h1>Your job search workspace</h1>
        <p className="intro">Create your profile, discover relevant offers, and understand your fit before applying.</p>
      </header>

      {(message || error) && <p className={error ? "notice error" : "notice"}>{error || message}</p>}

      <section className="grid">
        <form className="card" onSubmit={saveProfile}>
          <h2>Professional profile</h2>
          <label>Full name<input required value={profile.fullName} onChange={(event) => setProfile({ ...profile, fullName: event.target.value })} /></label>
          <label>Email<input required type="email" value={profile.email} onChange={(event) => setProfile({ ...profile, email: event.target.value })} /></label>
          <label>Professional title<input value={profile.professionalTitle} onChange={(event) => setProfile({ ...profile, professionalTitle: event.target.value })} /></label>
          <label>Preferred location<input value={profile.preferredLocation} onChange={(event) => setProfile({ ...profile, preferredLocation: event.target.value })} /></label>
          <label>Skills <span className="hint">(comma separated)</span><input value={profile.skills.join(", ")} onChange={(event) => updateSkills(event.target.value)} /></label>
          <button type="submit">Save profile</button>
        </form>

        <section className="card">
          <div className="section-heading">
            <div><h2>Job offers</h2><p className="hint">Search your saved opportunities.</p></div>
            <span className="count">{jobs.length}</span>
          </div>
          <form className="search" onSubmit={(event) => { event.preventDefault(); void loadJobs(keyword); }}>
            <input placeholder="Search title, company, or description" value={keyword} onChange={(event) => setKeyword(event.target.value)} />
            <button type="submit">Search</button>
          </form>
          <div className="jobs">
            {jobs.length === 0 ? <p className="hint">No job offers yet. Add one through the API to begin matching.</p> : jobs.map((job) => (
              <article className="job" key={job.id}>
                <div><h3>{job.title}</h3><p>{job.company} · {job.location || "Location not specified"}</p></div>
                <span className="status">{job.status}</span>
                <p className="skills">{job.skills.join(" · ")}</p>
                <div className="job-actions">
                  <button type="button" onClick={() => void createApplication(job.id)}>Track application</button>
                  <button type="button" onClick={() => void generateDocument(job.id, "CV")}>Generate CV</button>
                  <button type="button" onClick={() => void generateDocument(job.id, "COVER_LETTER")}>Generate letter</button>
                </div>
              </article>
            ))}
          </div>
        </section>

        <form className="card" onSubmit={saveJob}>
          <h2>Add a job offer</h2>
          <label>Job title<input required value={jobDraft.title} onChange={(event) => setJobDraft({ ...jobDraft, title: event.target.value })} /></label>
          <label>Company<input required value={jobDraft.company} onChange={(event) => setJobDraft({ ...jobDraft, company: event.target.value })} /></label>
          <label>Location<input value={jobDraft.location} onChange={(event) => setJobDraft({ ...jobDraft, location: event.target.value })} /></label>
          <label>Skills <span className="hint">(comma separated)</span><input value={jobDraft.skills} onChange={(event) => setJobDraft({ ...jobDraft, skills: event.target.value })} /></label>
          <label>Description<textarea value={jobDraft.description} onChange={(event) => setJobDraft({ ...jobDraft, description: event.target.value })} /></label>
          <button type="submit">Save job offer</button>
        </form>

        <section className="card">
          <h2>Application dashboard</h2>
          <p className="metric">{dashboard?.total ?? applications.length} <span>tracked applications</span></p>
          <div className="status-list">
            {dashboard && Object.entries(dashboard.byStatus).map(([status, total]) => (
              <span key={status} className="status">{status}: {total}</span>
            ))}
          </div>
          {applications.length === 0 && <p className="hint">Create an application from a saved job offer.</p>}
        </section>
      </section>
    </main>
  );
}

createRoot(document.getElementById("root")!).render(<App />);
