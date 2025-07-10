
import re

def convert_latex_to_markdown(text):
    # Pattern to match the entire LaTeX block
    pattern = r"\\\[(.*?)\\\]"
    
    # Function to replace each match with markdown LaTeX block
    def replacer(match):
        content = match.group(1).strip()
        return f"$$\n{content}\n$$"

    # Replace using re.sub with DOTALL to capture multiline LaTeX
    new_text = re.sub(pattern, replacer, text, flags=re.DOTALL)
    
    return new_text