# Importing necessary libraries
from openai import OpenAI
from parser import code_to_file, extract_filename, run_code

# Setting up the API
class OpenAIClient:
    def __init__(self, base_url, api_key, model):
        self.client = OpenAI(base_url=base_url, api_key=api_key)
        self.model = model  # Store the model

    def get_response(self, messages, temperature=0.8):
        return self.client.chat.completions.create(model=self.model, messages=messages, temperature=temperature)
    
# Defining the main class for code generation and execution
class CodeExecutor:
    def __init__(self, api_client):
        self.api_client = api_client

    def generate_code(self, query, docker_name):
        prompt = self._create_prompt(query)
        raw_response = self._get_raw_response(prompt)
        refined_response = self._refine_response(raw_response)
        file_name = self._save_code(refined_response)
        return self._execute_code(file_name, docker_name)

    def _create_prompt(self, query):
        print("\n_create_prompt WIP")
        return f"{query}\nFormat the response in the following format:\n1. plan\n2. filename\n3. Code\n\nDo not show any comments. The code should not have multi-line comments. Only single-line comments are permissible."


    def _get_raw_response(self, prompt):
        response = self.api_client.get_response(
            messages=[
                {"role": "system", "content": "You are a helpful coding assistant"},
                {"role": "user", "content": prompt}
            ]
        )
        print("\n_get_raw_response WIP")
        return response.choices[0].message.content

    def _refine_response(self, raw_response):
        response = self.api_client.get_response(
            messages=[
                {"role": "system", "content": "You are a helpful assistant. There are six conditions. Think carefully and follow the conditions strictly."},
                {"role": "user", "content": self._refinement_instructions(raw_response)}
            ]
        )
        print("\n_refine_response WIP")
        return response.choices[0].message.content

    def _refinement_instructions(self, raw_response):
        return f"""You will analyze the text given, follow the instructions and provide the response.
        Instructions:
        1. Enclose your response in following xml format tags: <code> and </code>.
        2. Save the filename and code in dictionary format. keys will be 'filename' and 'code'. {{filename_key: filename_value, code_key: code_value}}
        3. Within the dictionary, in the code key if you detect the python code use markdown blocks ```python in the beginning and ``` in the end.
        4. Use escaped triple quotes (`\"\"\"`) for the value of the key instead of triple quotes.
        5. If you detect multi-line comments in triple quotes within the value of the code, remove those comments. Use single-line comments.
        6. Ensure you have followed the correct openings and closings like <code> </code> tags and {{ }} curly brackets.

        ### Example ### 
        <code>
        {{
          "filename": "hello.py",
          "code": ```python
          print("Hello world!")
          ```
        }}
        </code>

        Here is the text for you: {raw_response}"""
    
        print("_refinement_instructions WIP")

    def _save_code(self, response_refine):
        print("_save_code WIP")
        code_to_file(response_refine)
        return extract_filename(response_refine)

    def _execute_code(self, file_name, docker_name):
        print("_execute_code WIP")
        result_run_code = run_code(file_name, docker_name)
        print(file_name, result_run_code[0], result_run_code[1])
        return file_name, result_run_code[0], result_run_code[1]
                
    def fix_code(self, code_file, code_content, error_message):
        code_content = read_file(code_file)
        fix_response = self.api_client.get_response(
            messages=[
                {"role": "system", "content": "You are an expert in fixing coding. You will analyze the given code and error and fix the code. You will respond in following format: \n1. Diagnosis \n2. filename \n3. Code"},
                {"role": "user", "content": f"Here are the details for you to fix the code \n filename: {code_file} \n code: {code_content} \n\n error: {error_message}"}
            ]
        )
        return self._refine_fix_response(fix_response.choices[0].message.content)

    def _refine_fix_response(self, fix_response_raw):
        refined_response = self.api_client.get_response(
            messages=[
                {"role": "system", "content": "You are an expert in coding, identifying bugs and solving."},
                {"role": "user", "content": self._fix_instructions(fix_response_raw)}
            ]
        )
        code_to_file(refined_response.choices[0].message.content)
        return extract_filename(refined_response.choices[0].message.content), run_code(extract_filename(refined_response.choices[0].message.content), docker_name)

    def _fix_instructions(self, fix_response_raw):
        return f"""You will analyze the text given, follow the instructions and provide the response.
        Instructions:
        1. Enclose your response in following xml format tags: <code> and </code>.
        2. Save the filename and code in dictionary format. keys will be 'filename' and 'code'. {{filename_key: filename_value, code_key: code_value}}
        3. Within the dictionary, in the code key if you detect the python code use markdown blocks ```python in the beginning and ``` in the end.
        4. Use escaped triple quotes (`\"\"\"`) for the value of the key instead of triple quotes.
        5. If you detect multi-line comments in triple quotes within the value of the code, remove those comments. Use single-line comments.
        6. Ensure you have followed the correct openings and closings like <code> </code> tags and {{ }} curly brackets.

        Here are the details for you: {fix_response_raw}"""

# Utility functions
def read_file(file_path):
    try:
        with open(file_path, 'r') as file:
            return file.read()
    except FileNotFoundError:
        print(f"Sorry, the file {file_path} does not exist.")
        return None
    
# Setting up CodingAgent
class CodingAgent:
    def __init__(self, api_client):
        self.code_executor = CodeExecutor(api_client=api_client)

    def execute_query(self, query, docker_name):
        # Generate and execute code
        result_code_gen_exec = self.code_executor.generate_code(query, docker_name)

        # Unpack results
        code_file, result_file, exit_code = result_code_gen_exec
        
        # Initialize variables for error and success
        var_error = None
        var_success = None

        # Handle success or error
        if exit_code == "exit code: 1: fail":
            var_error = read_file(result_file)
        elif exit_code == "exit code: 0: success":
            var_success = read_file(result_file)

        # Read code content
        code_content = read_file(code_file)

        # Fix the code if there was an error
        if var_error is not None:
            result_code_fix_exec = self.code_executor.fix_code(code_file, code_content, var_error)
            # You may want to read the fixed result again here if needed
            return code_content, var_error, result_code_fix_exec
        
        return code_content, var_success

def run_coding_agent(api_client_details, query, docker_name):
    api_client = OpenAIClient(**api_client_details)
    agent = CodingAgent(api_client)
    return agent.execute_query(query, docker_name)

# Main execution flow (can be left here or removed if not needed)
if __name__ == "__main__":
    api_client_details = {
        'base_url': 'http://localhost:11434/v1',
        'api_key': 'ollama',
        'model': "qwen2.5:14b-instruct-q5_K_M"
    }
    query = "Write a python program to count the r's in 'Strawberry'"
    docker_name = 'septimus'

    code_content, result = run_coding_agent(api_client_details, query, docker_name)
    print("Code Content:\n", code_content)
    print("Result:\n", result)