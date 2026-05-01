## 2024-03-27 - Streamlit Expander Icons
**Learning:** Adding icons to Streamlit `st.expander` components significantly improves the scannability of long lists of configuration options, providing immediate visual cues without taking up extra space.
**Action:** Utilize the `icon` parameter for `st.expander` and similar container widgets in Streamlit to enhance visual hierarchy and ease of use, especially in sidebars with many settings.

## 2024-05-01 - Error Prevention via Disabled States
**Learning:** Preventing users from selecting conflicting options (like checking "Replace Color with Transparency" when the output format is JPEG/BMP) is a more effective and pleasant UX pattern than allowing the selection and then displaying a warning or error message. It shifts the interface from error recovery to error prevention.
**Action:** When UI options are mutually exclusive or unsupported based on previous selections, explicitly disable the unavailable controls (`disabled=True` in Streamlit) and update the `help` text or provide a `st.caption` to explain why the option is unavailable, rather than waiting to show an error state later.
