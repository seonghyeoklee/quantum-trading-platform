package com.quantum.core.domain.port.eventsourcing;

import com.quantum.core.application.command.StreamCommand;

/** Interface for handling commands */
@FunctionalInterface
public interface CommandHandler {

    /**
     * Handle a command
     *
     * @param command the command to handle
     * @return result of command execution
     */
    CommandResult handle(StreamCommand command);

    /**
     * Indicates if this handler can handle the given command type
     *
     * @param commandType the command type
     * @return true if this handler can process the command type
     */
    default boolean canHandle(String commandType) {
        return true; // Default implementation accepts all commands
    }

    /** Result of command execution */
    class CommandResult {
        private final boolean success;
        private final String message;
        private final Object result;

        public CommandResult(boolean success, String message, Object result) {
            this.success = success;
            this.message = message;
            this.result = result;
        }

        public static CommandResult success(Object result) {
            return new CommandResult(true, "Command executed successfully", result);
        }

        public static CommandResult success(String message, Object result) {
            return new CommandResult(true, message, result);
        }

        public static CommandResult failure(String message) {
            return new CommandResult(false, message, null);
        }

        public boolean isSuccess() {
            return success;
        }

        public String getMessage() {
            return message;
        }

        public Object getResult() {
            return result;
        }
    }
}
