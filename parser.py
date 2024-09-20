# dts_parser.py
import json
import re
import subprocess

def to_json(input_str):
    pattern = r"<DTS>(.*?)</DTS>"
    match = re.search(pattern, input_str, re.DOTALL)

    if match:
        dict_str = match.group(1).strip()
        dict_str = re.sub(r'^\s*\w+\s*=\s*', '', dict_str)
        dict_str = dict_str.replace("'", '"')

        try:
            job_dict = json.loads(dict_str)
            return json.dumps(job_dict, indent=4)
        except json.JSONDecodeError as e:
            return f"Error parsing JSON: {e}"

    return "DTS tags not found"

def code_to_file(text: str): 
    try:
        # Step 1: Extract the content within the <code> and </code> tags
        code_block = re.search(r"<code>(.*?)<\/code>", text, re.DOTALL)
        
        if not code_block:
            raise ValueError("No <code> block found")

        content = code_block.group(1).strip()

        # Step 2: Extract the filename and code using regex
        filename_match = re.search(r'"filename":\s*"(.*?)"', content)
        # Match code enclosed by either """ or ``` (```python also supported)
        code_match = re.search(r'"code":\s*("""|```python|```)(.*?)(```|""")', content, re.DOTALL)

        if not filename_match:
            raise ValueError("Filename not found in the input")
        
        if not code_match:
            raise ValueError("Code block not found in the input")

        filename = filename_match.group(1)
        code = code_match.group(2)

        # Step 3: Remove any lingering markdown delimiters (``` or """)
        code = re.sub(r"^```.*|\"\"\"", "", code, flags=re.DOTALL).strip()

        # Step 4: Create the file with the extracted filename and write the code content to it
        with open(filename, 'w') as file:
            file.write(code)

        # If everything succeeds
        print("exit code: 0; success")
    
    except Exception as e:
        # Print the error message with exit code 1 if any exception occurs
        print(f"exit code: 1; failure reason: {str(e)}")

def extract_filename(input_str: str) -> str:
    # Remove the <code> and </code> tags
    cleaned_str = re.sub(r'</?code>', '', input_str)
    
    # Remove the triple backticks around the Python code
    cleaned_str = re.sub(r'```python[\s\S]+```', '""', cleaned_str)

    # Convert the remaining string into a dictionary
    try:
        # Safely load the JSON
        data = json.loads(cleaned_str.strip())
        return data.get("filename", "Filename not found")
    except json.JSONDecodeError as e:
        return f"Invalid JSON format: {e}"

def run_code(filename, docker_image):
    try:
        # Format the docker command with the filename and docker image
        command = fr'docker run --rm -v "C:/Users/CSC/Playground/":/app {docker_image} python /app/{filename}'
        
        # Run the docker command
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            # Return the error message as a string
            return f"Error: {result.stderr}"
    
    except subprocess.CalledProcessError as e:
        print(f"Command failed with exit code {e.returncode}: {e.output.strip()}")
        return f"Error: Command failed with exit code {e.returncode}"
    
    except Exception as e:
        print(f"Unexpected error: {e}")
        return "Error: Unexpected error"