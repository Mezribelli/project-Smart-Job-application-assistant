package com.smartjobs.matching;

import java.util.List;

public record MatchResponse(int score, List<String> matchingSkills, List<String> missingSkills, String recommendation) {
}
