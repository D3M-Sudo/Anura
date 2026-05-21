# test_extracted_page_reflow.py
#
# Static verification of the dynamic reflow bug fix in extracted_page.ui.

from pathlib import Path
import xml.etree.ElementTree as ET

PROJECT_ROOT = Path(__file__).resolve().parent.parent

def test_extracted_page_ui_reflow_properties() -> None:
    """
    Verifies that the generated extracted_page.ui contains the correct properties
    to enable dynamic text reflow as specified in the resolution methodology.
    """
    ui_file = PROJECT_ROOT / "data" / "ui" / "extracted_page.ui"
    assert ui_file.exists(), "extracted_page.ui must exist (run blueprint-compiler first)"

    tree = ET.parse(ui_file)
    root = tree.getroot()

    # Check ScrolledWindow (text_scrollview)
    scrollview = None
    for obj in root.iter("object"):
        if obj.get("id") == "text_scrollview" and obj.get("class") == "GtkScrolledWindow":
            scrollview = obj
            break

    assert scrollview is not None, "GtkScrolledWindow with id 'text_scrollview' not found"

    width_request = None
    hscrollbar_policy = None
    for prop in scrollview.findall("property"):
        if prop.get("name") == "width-request":
            width_request = prop.text
        if prop.get("name") == "hscrollbar-policy":
            hscrollbar_policy = prop.text

    assert width_request == "150", "text_scrollview must have width-request set to 150"
    assert hscrollbar_policy == "2", "text_scrollview must have hscrollbar-policy set to GTK_POLICY_NEVER (2)"

    # Check TextView (text_view)
    textview = None
    for obj in root.iter("object"):
        if obj.get("id") == "text_view" and obj.get("class") == "GtkTextView":
            textview = obj
            break

    assert textview is not None, "GtkTextView with id 'text_view' not found"

    wrap_mode = None
    left_margin = None
    right_margin = None
    for prop in textview.findall("property"):
        if prop.get("name") == "wrap-mode":
            wrap_mode = prop.text
        if prop.get("name") == "left-margin":
            left_margin = prop.text
        if prop.get("name") == "right-margin":
            right_margin = prop.text

    assert wrap_mode == "2", "text_view must have wrap-mode set to GTK_WRAP_WORD (2)"
    assert left_margin == "14", "text_view must have left-margin set to 14"
    assert right_margin == "14", "text_view must have right-margin set to 14"
