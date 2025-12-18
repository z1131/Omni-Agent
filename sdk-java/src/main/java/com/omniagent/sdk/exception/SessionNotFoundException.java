package com.omniagent.sdk.exception;

public class SessionNotFoundException extends OmniAgentException {
    private final String sessionId;
    
    public SessionNotFoundException(String sessionId) {
        super("Session not found: " + sessionId, 1003);
        this.sessionId = sessionId;
    }
    
    public String getSessionId() {
        return sessionId;
    }
}
