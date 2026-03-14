import asyncio
import os
import sys

sys.path.append(os.getcwd())

from app.services.extraction import extract_from_document
from app.config import settings

async def main():
    settings.use_mock_extraction = False
    
    sample_path = os.path.join(os.path.dirname(__file__), '..', 'samples', '32B418454.pdf')
    sample_path = os.path.abspath(sample_path)
    print(f"Testing extraction with {sample_path}")
    
    with open(sample_path, "rb") as f:
        pdf_bytes = f.read()

    print("Calling extract_from_document...")
    result = await extract_from_document(pdf_bytes, "application/pdf")
    
    print("\nExtraction Success!")
    print(f"Page {result.eCVI.PageNumber} / {result.eCVI.TotalPages}")
    print(f"Total Animals on form: {result.eCVI.TotalAnimals}")
    print(f"Number of animal rows parsed: {len(result.eCVI.Animals)}")
    
    if result.eCVI.Animals:
        for idx, animal in enumerate(result.eCVI.Animals):
            print(f"- Row {idx+1}: HeadCount={animal.HeadCount}, Species={animal.SpeciesCode}")
            for tag in animal.Tags:
                 print(f"  - Tag: {tag.TagType} {tag.Number}")
                 
    print("\nFull Result JSON:")
    print(result.model_dump_json(indent=2))

if __name__ == "__main__":
    asyncio.run(main())
