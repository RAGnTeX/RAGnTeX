"""This module provides tools to work with LaTeX Beamer presentations."""


def replace_unicode_greek(text):
    """Replace Greek Unicode characters with LaTeX equivalents.
    Args:
        text (str): Input text containing Greek characters.
    Returns:
        str: Text with Greek characters replaced by LaTeX commands.
    """
    greek_map = {
        'α': r'$\alpha$', 'β': r'$\beta$', 'γ': r'$\gamma$',
        'δ': r'$\delta$', 'ε': r'$\epsilon$', 'ζ': r'$\zeta$',
        'η': r'$\eta$', 'θ': r'$\theta$', 'ι': r'$\iota$',
        'κ': r'$\kappa$', 'λ': r'$\lambda$', 'μ': r'$\mu$',
        'ν': r'$\nu$', 'ξ': r'$\xi$', 'ο': 'o', 'π': r'$\pi$',
        'ρ': r'$\rho$', 'σ': r'$\sigma$', 'ς': r'$\varsigma$',
        'τ': r'$\tau$', 'υ': r'$\upsilon$', 'φ': r'$\phi$',
        'χ': r'$\chi$', 'ψ': r'$\psi$', 'ω': r'$\omega$',
        'Α': 'A', 'Β': 'B', 'Γ': r'$\Gamma$', 'Δ': r'$\Delta$',
        'Ε': 'E', 'Ζ': 'Z', 'Η': 'H', 'Θ': r'$\Theta$',
        'Ι': 'I', 'Κ': 'K', 'Λ': r'$\Lambda$', 'Μ': 'M',
        'Ν': 'N', 'Ξ': r'$\Xi$', 'Ο': 'O', 'Π': r'$\Pi$',
        'Ρ': 'P', 'Σ': r'$\Sigma$', 'Τ': 'T', 'Υ': r'$\Upsilon$',
        'Φ': r'$\Phi$', 'Χ': 'X', 'Ψ': r'$\Psi$', 'Ω': r'$\Omega$',
        'ϕ': r'$\varphi$', 'ϑ': r'$\vartheta$', 'ϰ': r'$\varkappa$', 'ϱ': r'$\varrho$',
    }

    for char, replacement in greek_map.items():
        text = text.replace(char, replacement)

    return text


def escape_latex_special_chars(text):
    """Escape selected LaTeX special characters.
    Args:
        text (str): Input text to escape.
    Returns:
        str: Text with LaTeX special characters escaped.
    """
    chars_map = {
        '%': r'\%',
    }

    for char, replacement in chars_map.items():
        text = text.replace(char, replacement)

    return text