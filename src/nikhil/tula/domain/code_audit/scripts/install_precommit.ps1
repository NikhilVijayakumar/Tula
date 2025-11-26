# Install pre-commit hooks
pip install pre-commit

# Install hooks for this repository
cd e:\Python\Amsha
pre-commit install

# Optional: Install OpenAI for AI-powered review
pip install openai

# Set OpenAI API key (if using AI review)
# $env:OPENAI_API_KEY='your-key-here'  # Add this to your PowerShell profile

# Test the setup
pre-commit run --all-files
