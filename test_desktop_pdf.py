"""
Quick test script for desktop build PDF generation.
Run this while the desktop app is running in the background.
"""
import urllib.request
import urllib.parse
from datetime import datetime, timedelta

def test_health():
    """Check if server is up on any common port."""
    for port in range(5000, 5007):
        try:
            url = f'http://127.0.0.1:{port}/health'
            with urllib.request.urlopen(url, timeout=1) as response:
                if response.status == 200:
                    print(f"✓ Server running on port {port}")
                    return port
        except Exception:
            continue
    print("✗ No server found on ports 5000-5006")
    return None

def test_pdf_generation(port):
    """Test PDF generation endpoint."""
    start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    end_date = datetime.now().strftime('%Y-%m-%d')
    
    data = urllib.parse.urlencode({
        'start_date': start_date,
        'end_date': end_date
    }).encode('utf-8')
    
    url = f'http://127.0.0.1:{port}/report/pdf'
    
    try:
        req = urllib.request.Request(
            url, 
            data=data, 
            method='POST',
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
        with urllib.request.urlopen(req, timeout=30) as response:
            if response.status == 200:
                pdf_data = response.read()
                content_type = response.headers.get('Content-Type', '')
                
                if content_type.startswith('application/pdf'):
                    print(f"✓ PDF generation successful")
                    print(f"  Status: {response.status}")
                    print(f"  Content-Type: {content_type}")
                    print(f"  Size: {len(pdf_data)} bytes")
                    
                    # Save to file
                    with open('desktop_test_report.pdf', 'wb') as f:
                        f.write(pdf_data)
                    print(f"  Saved as: desktop_test_report.pdf")
                    return True
                else:
                    print(f"✗ Wrong content type: {content_type}")
                    return False
            else:
                print(f"✗ Unexpected status: {response.status}")
                return False
    except Exception as e:
        print(f"✗ PDF generation failed: {e}")
        return False

if __name__ == '__main__':
    print("Testing desktop build...")
    print()
    
    # Test 1: Health check
    port = test_health()
    if not port:
        print("\n⚠ Server not running. Start the desktop app first:")
        print("  .\\dist\\ActivityTracker\\ActivityTracker.exe")
        exit(1)
    
    print()
    
    # Test 2: PDF generation
    success = test_pdf_generation(port)
    
    print()
    if success:
        print("✓ All tests passed!")
        exit(0)
    else:
        print("✗ Tests failed")
        exit(1)
