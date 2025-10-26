import chromadb
import os
from typing import List, Dict, Optional
from sentence_transformers import SentenceTransformer
import json
from pathlib import Path

class VectorDatabase:
    def __init__(self, db_path: str = "./vector_db"):
        self.db_path = db_path
        self.client = chromadb.PersistentClient(path=db_path)
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

        # Initialize collections
        self.loan_requirements_collection = self._get_or_create_collection("loan_requirements")
        self.compliance_collection = self._get_or_create_collection("compliance")
        self.red_flags_collection = self._get_or_create_collection("red_flags")

    def _get_or_create_collection(self, collection_name: str):
        """Get existing collection or create new one"""
        try:
            return self.client.get_collection(collection_name)
        except:
            return self.client.create_collection(collection_name)

    def add_knowledge_base(self, knowledge_base_path: str):
        """Load and embed all knowledge base documents"""
        print("Loading knowledge base into vector database...")

        # Process loan requirements
        req_path = os.path.join(knowledge_base_path, "loan_requirements")
        if os.path.exists(req_path):
            self._process_directory(req_path, self.loan_requirements_collection, "loan_requirement")

        # Process compliance documents
        comp_path = os.path.join(knowledge_base_path, "compliance")
        if os.path.exists(comp_path):
            self._process_directory(comp_path, self.compliance_collection, "compliance")

        # Process red flags
        flags_path = os.path.join(knowledge_base_path, "red_flags")
        if os.path.exists(flags_path):
            self._process_directory(flags_path, self.red_flags_collection, "red_flag")

        print("Knowledge base loaded successfully!")

    def _process_directory(self, directory_path: str, collection, doc_type: str):
        """Process all text files in a directory"""
        for file_path in Path(directory_path).glob("*.txt"):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Split content into chunks
            chunks = self._chunk_text(content)

            for i, chunk in enumerate(chunks):
                doc_id = f"{doc_type}_{file_path.stem}_{i}"
                embedding = self.embedding_model.encode(chunk).tolist()

                collection.add(
                    documents=[chunk],
                    embeddings=[embedding],
                    metadatas=[{
                        "source": str(file_path),
                        "type": doc_type,
                        "chunk_id": i,
                        "filename": file_path.name
                    }],
                    ids=[doc_id]
                )

    def _chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Split text into overlapping chunks"""
        words = text.split()
        chunks = []

        for i in range(0, len(words), chunk_size - overlap):
            chunk_words = words[i:i + chunk_size]
            chunk = " ".join(chunk_words)
            chunks.append(chunk)

            if i + chunk_size >= len(words):
                break

        return chunks

    def search_requirements(self, query: str, n_results: int = 5) -> List[Dict]:
        """Search loan requirements"""
        return self._search_collection(self.loan_requirements_collection, query, n_results)

    def search_compliance(self, query: str, n_results: int = 5) -> List[Dict]:
        """Search compliance information"""
        return self._search_collection(self.compliance_collection, query, n_results)

    def search_red_flags(self, query: str, n_results: int = 5) -> List[Dict]:
        """Search red flag patterns"""
        return self._search_collection(self.red_flags_collection, query, n_results)

    def search_all(self, query: str, n_results: int = 3) -> Dict:
        """Search across all collections"""
        return {
            "requirements": self.search_requirements(query, n_results),
            "compliance": self.search_compliance(query, n_results),
            "red_flags": self.search_red_flags(query, n_results)
        }

    def _search_collection(self, collection, query: str, n_results: int) -> List[Dict]:
        """Search a specific collection"""
        query_embedding = self.embedding_model.encode(query).tolist()

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )

        formatted_results = []
        if results['documents'] and results['documents'][0]:
            for i in range(len(results['documents'][0])):
                formatted_results.append({
                    "content": results['documents'][0][i],
                    "metadata": results['metadatas'][0][i],
                    "distance": results['distances'][0][i] if 'distances' in results else 0
                })

        return formatted_results

    def add_document_to_knowledge(self, content: str, doc_type: str, metadata: Dict):
        """Add a new document to the knowledge base"""
        collection_map = {
            "loan_requirement": self.loan_requirements_collection,
            "compliance": self.compliance_collection,
            "red_flag": self.red_flags_collection
        }

        collection = collection_map.get(doc_type)
        if not collection:
            raise ValueError(f"Unknown document type: {doc_type}")

        chunks = self._chunk_text(content)

        for i, chunk in enumerate(chunks):
            doc_id = f"{doc_type}_{metadata.get('filename', 'unknown')}_{i}"
            embedding = self.embedding_model.encode(chunk).tolist()

            collection.add(
                documents=[chunk],
                embeddings=[embedding],
                metadatas=[{**metadata, "chunk_id": i}],
                ids=[doc_id]
            )

    def get_collection_stats(self) -> Dict:
        """Get statistics about collections"""
        stats = {}
        collections = [
            ("loan_requirements", self.loan_requirements_collection),
            ("compliance", self.compliance_collection),
            ("red_flags", self.red_flags_collection)
        ]

        for name, collection in collections:
            try:
                count = collection.count()
                stats[name] = {"document_count": count}
            except:
                stats[name] = {"document_count": 0}

        return stats

    def delete_collection(self, collection_name: str):
        """Delete a collection"""
        try:
            self.client.delete_collection(collection_name)
            print(f"Collection {collection_name} deleted successfully")
        except:
            print(f"Failed to delete collection {collection_name}")

    def reset_database(self):
        """Reset all collections"""
        collections = ["loan_requirements", "compliance", "red_flags"]
        for collection_name in collections:
            self.delete_collection(collection_name)

        # Recreate collections
        self.loan_requirements_collection = self._get_or_create_collection("loan_requirements")
        self.compliance_collection = self._get_or_create_collection("compliance")
        self.red_flags_collection = self._get_or_create_collection("red_flags")