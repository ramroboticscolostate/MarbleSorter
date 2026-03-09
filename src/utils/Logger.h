#ifndef LOGGER_H
#define LOGGER_H

#include <string>

// Log header for different event to be included/referenced through files we add.TO log state and catch issues and where
//how to utilize in other files ex.info: Logger::info("current Marble analysis returned {color}")
enum class LogType {
    INFO,
    WARN,
    ERROR,
    STATE
};

using MessageRef = const std::string&;

class Logger{

    public:
        static void log(LogType type, MessageRef message);

        static void info(MessageRef message);
        static void warn(MessageRef message);
        static void error(MessageRef message);
        static void state(MessageRef message);

    private:
        static std::string levelToString(LogType type);
};

#endif

