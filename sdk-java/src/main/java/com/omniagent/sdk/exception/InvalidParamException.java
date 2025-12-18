package com.omniagent.sdk.exception;

public class InvalidParamException extends OmniAgentException {
    private final String param;
    
    public InvalidParamException(String param, String reason) {
        super("Invalid parameter '" + param + "': " + reason, 1002);
        this.param = param;
    }
    
    public String getParam() {
        return param;
    }
}
