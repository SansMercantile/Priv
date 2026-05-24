# priv/backend/cpp_module/cpp_server.py
import ctypes
import os
import logging
from flask import Flask, request, jsonify
from threading import Thread # For running Flask in a separate thread if needed, though Gunicorn handles this.

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# --- C++ Bridge Setup ---
class FinancialCppBridge:
    """
    A bridge to call high-performance C++ functions from a compiled library.
    This is similar to the existing Swift bridge, but specifically for C++.
    """
    def __init__(self, library_path: str = "./libfinancial_calculator.so"):
        self.cpp_lib = None
        try:
            # Check if the library file exists before attempting to load
            if not os.path.exists(library_path):
                raise FileNotFoundError(f"C++ shared library not found at path: {library_path}")

            # Load the compiled C++ shared library
            self.cpp_lib = ctypes.CDLL(library_path)
            
            # Define function signature: double calculate_compound_interest_cpp(double, double, int)
            self.calculate_compound_interest_cpp = self.cpp_lib.calculate_compound_interest_cpp
            self.calculate_compound_interest_cpp.argtypes = [ctypes.c_double, ctypes.c_double, ctypes.c_int]
            self.calculate_compound_interest_cpp.restype = ctypes.c_double
            
            logger.info(f"Successfully loaded C++ library from {library_path} and bridged functions.")

        except FileNotFoundError as e:
            logger.error(f"C++ bridge disabled: {e}. Ensure the shared library is compiled and accessible.")
            self.cpp_lib = None
        except Exception as e:
            logger.error(f"Failed to load C++ library or bridge functions: {e}", exc_info=True)
            self.cpp_lib = None

    def is_available(self) -> bool:
        """Check if the C++ library was loaded successfully."""
        return self.cpp_lib is not None

    def calculate_interest(self, principal: float, rate: float, years: int) -> float:
        """
        Executes a financial calculation by calling the C++ function.
        """
        if not self.is_available():
            logger.error("Cannot execute C++ task: Financial C++ bridge is not available.")
            raise RuntimeError("C++ module not available.")
        
        logger.info(f"Calling C++ module to perform calculation with inputs: P={principal}, R={rate}, Y={years}")
        result = self.calculate_compound_interest_cpp(principal, rate, years)
        logger.info(f"Received result from C++ module: {result}")
        return result

# Initialize the C++ bridge globally for the Flask app
cpp_bridge = FinancialCppBridge()

# --- Flask Routes ---
@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint for health checks."""
    return jsonify({"status": "ok", "message": "C++ Financial Microservice is running."}), 200

@app.route('/calculate_compound_interest', methods=['POST'])
def calculate_interest_endpoint():
    """
    Endpoint to receive calculation requests and delegate to the C++ module.
    """
    if not cpp_bridge.is_available():
        return jsonify({"error": "C++ calculation module not loaded."}), 500

    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON payload."}), 400

    try:
        principal = float(data.get('principal'))
        rate = float(data.get('rate'))
        years = int(data.get('years'))

        if principal is None or rate is None or years is None:
            return jsonify({"error": "Missing required parameters: principal, rate, years."}), 400
        
        # Call the C++ function via the bridge
        result = cpp_bridge.calculate_interest(principal, rate, years)
        
        return jsonify({"result": result}), 200

    except ValueError:
        return jsonify({"error": "Invalid data types for principal, rate, or years. Must be numeric."}), 400
    except RuntimeError as e:
        logger.error(f"RuntimeError occurred: {e}", exc_info=True)
        return jsonify({"error": "Internal server error."}), 500
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)
        return jsonify({"error": "Internal server error."}), 500

if __name__ == '__main__':
    # When running with Gunicorn (as in Dockerfile CMD), this block is not executed.
    # It's for local development testing.
    port = int(os.environ.get("PORT", 8081))
    logger.info(f"Starting C++ Financial Microservice (Flask wrapper) on port {port}...")
    app.run(host='0.0.0.0', port=port, debug=False) # In production, use Gunicorn
