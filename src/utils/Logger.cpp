# include "Logger.h"
#include <iostream>

void Logger::log(LogType level, MessageRef message){
    std::cout << "[" << levelToString(level) << "] " << message << std::endl;
}

void Logger::info(MessageRef message){
    log(LogType::INFO, message);
}

void Logger::warn(MessageRef message){
    log(LogType::WARN, message);
}

void Logger::error(MessageRef message){
    log(LogType::ERROR, message);
}

void Logger::state(MessageRef message){
    log(LogType::STATE, message);
}

std::string Logger::levelToString(LogType level){

    switch(level){
        case LogType::INFO:
            return "INFO";
        case LogType::WARN:
            return "WARN";
        case LogType::ERROR:
            return "ERROR";
        case LogType::STATE:
            return "STATE";
        default:
            return "LOG";
    }
}

