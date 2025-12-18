package com.omniagent.sdk.exception;

public class TimeoutException extends OmniAgentException {
    public TimeoutException(String message) {
        super(message, 3001);
    }
}
