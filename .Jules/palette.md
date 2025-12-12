# Palette's Journal - Critical Learnings

## 2024-05-23 - Micro-UX in Streamlit
**Learning:** Streamlit abstracts away much of the HTML/CSS, so traditional accessibility fixes (like ARIA attributes on custom elements) are harder to apply directly. However, Streamlit provides parameters like `help` on most input widgets which render as tooltips. This is a powerful, built-in way to improve usability and accessibility (by explaining context) without needing custom HTML.
**Action:** Prioritize using the `help` parameter on all Streamlit widgets to provide context and instructions, especially for technical settings.
