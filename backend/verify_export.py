import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

try:
    from mock_data import generate_pdf_report
    print("Generating test PDF for B0005...")
    pdf_bytes = generate_pdf_report('B0005')
    
    if isinstance(pdf_bytes, bytes) and len(pdf_bytes) > 1000:
        print(f"SUCCESS: Generated PDF report ({len(pdf_bytes)} bytes)")
    else:
        print(f"FAILURE: Invalid PDF output. Got {type(pdf_bytes)} with length {len(pdf_bytes) if hasattr(pdf_bytes, '__len__') else 'N/A'}")
        
except Exception as e:
    print(f"CRITICAL ERROR: {e}")
    import traceback
    traceback.print_exc()
