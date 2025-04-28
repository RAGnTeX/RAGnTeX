import os
import subprocess


def CompilePresentation(latex_code, work_dir):
    # Remove possible Markdown wrapping around the output
    if latex_code.startswith("```latex"):
        latex_code = latex_code.split("\n", 1)[1]  # Remove the first line
    if latex_code.endswith("```"):
        latex_code = latex_code.rsplit("\n", 1)[0]

    # Save LaTeX code to file
    tex_file = os.path.join(work_dir, "presentation.tex")
    with open(tex_file, "w") as f:
        f.write(latex_code)

    print("=" * 100)
    print("📄 Files in the directory:")

    # List files in the directory using Python (instead of `!ls`)
    for file in os.listdir(work_dir):
        print(file)

    # Compile with pdflatex (using subprocess instead of `!`)
    os.chdir(work_dir)  # Change working directory

    try:
        # Run pdflatex twice to ensure proper slide enumeration
        subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", "presentation.tex"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", "presentation.tex"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    except subprocess.CalledProcessError as e:
        # Handle error in case of failed LaTeX compilation
        print("❌ PDF generation failed. Here's the log:")
        print(e.stderr.decode())
    else:
        # Check for PDF output
        if not os.path.exists("presentation.pdf"):
            print("❌ PDF generation failed. No PDF file found.")
        else:
            print(f"💾 PDF generated successfully in: {work_dir}")
