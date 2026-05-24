// priv/backend/cpp_module/main.cpp
#include <iostream> // Required for input/output operations
#include <string>   // Required for string manipulation
#include <stdexcept> // Required for standard exceptions like invalid_argument
#include <cmath>    // Required for mathematical functions like pow

// Function to calculate compound interest
// This function is designed to be called by an external system (e.g., Python via HTTP).
// In a real microservice, this would be part of a server's request handler.
extern "C" double calculate_compound_interest_cpp(double principal, double rate, int years) {
    // Log the incoming parameters for debugging purposes.
    std::cout << "C++ Microservice: Received request to calculate compound interest." << std::endl;
    std::cout << "  Principal: " << principal << std::endl;
    std::cout << "  Rate: " << rate << std::endl;
    std::cout << "  Years: " << years << std::endl;

    // Basic input validation
    if (principal < 0 || rate < 0 || years < 0) {
        // In a real HTTP service, this would return an error response.
        // For this example, we'll print an error and return 0.
        std::cerr << "C++ Microservice Error: Invalid input parameters (cannot be negative)." << std::endl;
        return 0.0; 
    }

    // Perform the compound interest calculation: P * (1 + r)^n
    double result = principal * std::pow(1.0 + rate, years);

    // Log the calculated result.
    std::cout << "C++ Microservice: Calculated result: " << result << std::endl;
    return result;
}

// A main function is included for local testing or if this were to be run as a standalone executable
// that takes command-line arguments, rather than directly bound via ctypes or serving HTTP.
// For a true HTTP microservice, this main function would typically initialize a web server.
int main(int argc, char* argv[]) {
    // This main function demonstrates how the C++ code *could* be used locally.
    // When deployed as a microservice, a web server framework (e.g., Crow, Boost.Beast)
    // would wrap `calculate_compound_interest_cpp` and expose it via HTTP.
    
    if (argc == 4) {
        try {
            double principal = std::stod(argv[1]); // Convert string to double
            double rate = std::stod(argv[2]);     // Convert string to double
            int years = std::stoi(argv[3]);       // Convert string to int
            
            double result = calculate_compound_interest_cpp(principal, rate, years);
            std::cout << "Local C++ execution result: " << result << std::endl;
        } catch (const std::invalid_argument& ia) {
            std::cerr << "Invalid argument: " << ia.what() << ". Please provide numeric values." << std::endl;
            return 1;
        } catch (const std::out_of_range& oor) {
            std::cerr << "Out of range: " << oor.what() << ". Numeric value too large or too small." << std::endl;
            return 1;
        }
    } else {
        std::cout << "Usage: " << argv[0] << " <principal> <rate> <years>" << std::endl;
        std::cout << "Example: " << argv[0] << " 1000 0.05 10" << std::endl;
    }
    return 0;
}
