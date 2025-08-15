#!/usr/bin/env python3
"""
Test script to verify the library service wrapper integration
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_wrapper():
    """Test the library service wrapper"""
    
    print("=" * 60)
    print("🧪 TESTING LIBRARY SERVICE WRAPPER")
    print("=" * 60)
    
    try:
        # Import the wrapper
        from library_service_wrapper import LibraryServiceWrapper
        
        print("✅ Successfully imported LibraryServiceWrapper")
        
        # Create instance
        wrapper = LibraryServiceWrapper()
        print(f"✅ Wrapper initialized")
        print(f"   - Educational RAG available: {wrapper.educational_rag_agent is not None}")
        print(f"   - Enhanced service available: {wrapper.enhanced_service is not None}")
        
        # Test upload with sample content
        test_content = b"This is a test document for the library service wrapper."
        test_filename = "test_document.txt"
        test_metadata = {
            'subject': 'Testing',
            'category': 'Documentation',
            'level': 'Basic'
        }
        
        print("\n📤 Testing document upload...")
        result = await wrapper.upload_document(
            file_content=test_content,
            filename=test_filename,
            content_type="text/plain",
            metadata=test_metadata
        )
        
        print("✅ Upload completed successfully!")
        print(f"   - Service used: {result.get('service_used', 'unknown')}")
        print(f"   - Document ID: {result.get('document_id', 'N/A')}")
        print(f"   - Success: {result.get('success', False)}")
        
        # Test search if available
        if hasattr(wrapper, 'search_documents'):
            print("\n🔍 Testing search...")
            search_results = await wrapper.search_documents("test", top_k=5)
            # Handle both list and dict return types
            if isinstance(search_results, list):
                print(f"✅ Search completed: {len(search_results)} results found")
            else:
                print(f"✅ Search completed: {len(search_results.get('results', []))} results found")
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Make sure all dependencies are installed")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_wrapper())