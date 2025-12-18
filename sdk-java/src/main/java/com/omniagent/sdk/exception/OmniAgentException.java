package com.omniagent.sdk.exception;

/**
 * Omni-Agent SDK 基础异常
 */
public class OmniAgentException extends RuntimeException {
    private final int code;
    
    public OmniAgentException(String message) {
        this(message, 0);
    }
    
    public OmniAgentException(String message, int code) {
        super(message);
        this.code = code;
    }
    
    public OmniAgentException(String message, Throwable cause) {
        super(message, cause);
        this.code = 0;
    }
    
    public int getCode() {
        return code;
    }
}
