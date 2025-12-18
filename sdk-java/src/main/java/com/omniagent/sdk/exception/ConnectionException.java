package com.omniagent.sdk.exception;

public class ConnectionException extends OmniAgentException {
    public ConnectionException(String message) {
        super(message, 1001);
    }
}
