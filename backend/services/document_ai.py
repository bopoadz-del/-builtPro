# Document AI Service - ITEM 110
# OCR, NLP, and intelligent document processing for construction documents

from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import re
from datetime import datetime
import json

from ..core.logging_config import get_logger

logger = get_logger(__name__)

# Try to import OCR libraries
try:
    import pytesseract
    from PIL import Image
    OCR_AVAILABLE = True
except ImportError:
    pytesseract = None
    Image = None
    OCR_AVAILABLE = False
    logger.info("Tesseract/PIL not installed - OCR features disabled")

# Try to import NLP libraries
try:
    import spacy
    NLP_AVAILABLE = True
except ImportError:
    spacy = None
    NLP_AVAILABLE = False
    logger.info("spaCy not installed - NLP features limited")


class DocumentType(str, Enum):
    """Construction document types."""
    DRAWING = "drawing"
    SPECIFICATION = "specification"
    RFI = "rfi"
    SUBMITTAL = "submittal"
    CHANGE_ORDER = "change_order"
    MEETING_MINUTES = "meeting_minutes"
    INSPECTION_REPORT = "inspection_report"
    INVOICE = "invoice"
    CONTRACT = "contract"
    OTHER = "other"


class EntityType(str, Enum):
    """Named entity types in construction documents."""
    COMPANY = "company"
    PERSON = "person"
    DATE = "date"
    MONEY = "money"
    LOCATION = "location"
    MATERIAL = "material"
    EQUIPMENT = "equipment"
    QUANTITY = "quantity"
    STANDARD = "standard"
    SECTION = "section"


@dataclass
class Entity:
    """Named entity extracted from document."""
    text: str
    type: EntityType
    start: int
    end: int
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DocumentMetadata:
    """Extracted document metadata."""
    title: Optional[str] = None
    document_number: Optional[str] = None
    revision: Optional[str] = None
    date: Optional[datetime] = None
    author: Optional[str] = None
    project: Optional[str] = None
    discipline: Optional[str] = None
    page_count: int = 0


@dataclass
class ProcessedDocument:
    """Processed document with extracted information."""
    id: str
    type: DocumentType
    raw_text: str
    cleaned_text: str
    metadata: DocumentMetadata
    entities: List[Entity] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    summary: Optional[str] = None
    action_items: List[str] = field(default_factory=list)
    key_dates: List[Tuple[str, datetime]] = field(default_factory=list)
    confidence: float = 0.0


class DocumentAIService:
    """
    Intelligent document processing service.

    Features:
    - OCR for scanned documents
    - Text extraction and cleaning
    - Named Entity Recognition (NER)
    - Document classification
    - Key information extraction
    - Action item detection
    - Summary generation
    """

    def __init__(self, spacy_model: str = "en_core_web_sm"):
        """
        Initialize Document AI service.

        Args:
            spacy_model: SpaCy model to use for NLP
        """
        self.logger = get_logger(self.__class__.__name__)
        self.nlp = None

        if NLP_AVAILABLE and spacy is not None:
            try:
                self.nlp = spacy.load(spacy_model)
                self.logger.info(f"Loaded spaCy model: {spacy_model}")
            except Exception as e:
                self.logger.warning(f"Failed to load spaCy model: {e}")

    def process_document(
        self,
        document_path: Path,
        document_type: Optional[DocumentType] = None
    ) -> ProcessedDocument:
        """
        Process a document end-to-end.

        Args:
            document_path: Path to document file
            document_type: Optional document type hint

        Returns:
            Processed document with extracted information
        """
        # Extract text
        raw_text = self._extract_text(document_path)

        # Clean text
        cleaned_text = self._clean_text(raw_text)

        # Classify document type if not provided
        if document_type is None:
            document_type = self._classify_document(cleaned_text)

        # Extract metadata
        metadata = self._extract_metadata(cleaned_text, document_type)

        # Extract entities
        entities = self._extract_entities(cleaned_text)

        # Extract keywords
        keywords = self._extract_keywords(cleaned_text)

        # Detect action items
        action_items = self._extract_action_items(cleaned_text)

        # Extract key dates
        key_dates = self._extract_key_dates(cleaned_text)

        # Generate summary
        summary = self._generate_summary(cleaned_text)

        # Calculate confidence
        confidence = self._calculate_confidence(raw_text, cleaned_text, entities)

        return ProcessedDocument(
            id=str(document_path),
            type=document_type,
            raw_text=raw_text,
            cleaned_text=cleaned_text,
            metadata=metadata,
            entities=entities,
            keywords=keywords,
            summary=summary,
            action_items=action_items,
            key_dates=key_dates,
            confidence=confidence
        )

    def _extract_text(self, document_path: Path) -> str:
        """Extract text from document (PDF, image, etc.)."""
        suffix = document_path.suffix.lower()

        if suffix in ['.jpg', '.jpeg', '.png', '.tiff', '.bmp']:
            return self._extract_text_from_image(document_path)
        elif suffix == '.pdf':
            return self._extract_text_from_pdf(document_path)
        elif suffix in ['.txt', '.md']:
            return document_path.read_text(encoding='utf-8')
        else:
            self.logger.warning(f"Unsupported file type: {suffix}")
            return ""

    def _extract_text_from_image(self, image_path: Path) -> str:
        """Extract text from image using OCR."""
        if not OCR_AVAILABLE or pytesseract is None or Image is None:
            self.logger.warning("OCR not available - cannot extract text from image")
            return ""

        try:
            image = Image.open(image_path)
            text = pytesseract.image_to_string(image)
            self.logger.info(f"Extracted {len(text)} characters from image")
            return text
        except Exception as e:
            self.logger.error(f"OCR failed: {e}")
            return ""

    def _extract_text_from_pdf(self, pdf_path: Path) -> str:
        """Extract text from PDF."""
        try:
            import PyPDF2

            text = []
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text.append(page.extract_text())

            result = '\n'.join(text)
            self.logger.info(f"Extracted {len(result)} characters from PDF")
            return result

        except ImportError:
            self.logger.warning("PyPDF2 not installed - cannot extract PDF text")
            return ""
        except Exception as e:
            self.logger.error(f"PDF extraction failed: {e}")
            return ""

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        # Remove extra whitespace
        cleaned = re.sub(r'\s+', ' ', text)

        # Remove special characters but keep punctuation
        cleaned = re.sub(r'[^\w\s.,;:!?()$%-]', '', cleaned)

        # Normalize line breaks
        cleaned = cleaned.replace('\r\n', '\n').replace('\r', '\n')

        return cleaned.strip()

    def _classify_document(self, text: str) -> DocumentType:
        """Classify document type based on content."""
        text_lower = text.lower()

        # Simple keyword-based classification
        if any(word in text_lower for word in ['rfi', 'request for information']):
            return DocumentType.RFI
        elif any(word in text_lower for word in ['submittal', 'shop drawing']):
            return DocumentType.SUBMITTAL
        elif any(word in text_lower for word in ['change order', 'co-']):
            return DocumentType.CHANGE_ORDER
        elif any(word in text_lower for word in ['meeting minutes', 'attendees']):
            return DocumentType.MEETING_MINUTES
        elif any(word in text_lower for word in ['inspection', 'site visit']):
            return DocumentType.INSPECTION_REPORT
        elif any(word in text_lower for word in ['invoice', 'payment', 'bill to']):
            return DocumentType.INVOICE
        elif any(word in text_lower for word in ['contract', 'agreement', 'whereas']):
            return DocumentType.CONTRACT
        elif any(word in text_lower for word in ['specification', 'section']):
            return DocumentType.SPECIFICATION
        elif any(word in text_lower for word in ['drawing', 'plan', 'elevation']):
            return DocumentType.DRAWING

        return DocumentType.OTHER

    def _extract_metadata(
        self,
        text: str,
        doc_type: DocumentType
    ) -> DocumentMetadata:
        """Extract document metadata."""
        metadata = DocumentMetadata()

        # Extract document number (e.g., "Doc No: A-101")
        doc_num_match = re.search(
            r'(?:doc(?:ument)?\.?\s*(?:no|number|#):?\s*)([A-Z0-9-]+)',
            text,
            re.IGNORECASE
        )
        if doc_num_match:
            metadata.document_number = doc_num_match.group(1)

        # Extract revision (e.g., "Rev: 3")
        rev_match = re.search(
            r'(?:rev(?:ision)?\.?\s*:?\s*)([A-Z0-9]+)',
            text,
            re.IGNORECASE
        )
        if rev_match:
            metadata.revision = rev_match.group(1)

        # Extract project name
        project_match = re.search(
            r'(?:project:?\s+)(.+?)(?:\n|$)',
            text,
            re.IGNORECASE
        )
        if project_match:
            metadata.project = project_match.group(1).strip()

        return metadata

    def _extract_entities(self, text: str) -> List[Entity]:
        """Extract named entities using NLP."""
        entities = []

        if self.nlp is None:
            # Fallback: Use regex patterns
            return self._extract_entities_regex(text)

        try:
            doc = self.nlp(text[:1000000])  # Limit text length

            for ent in doc.ents:
                entity_type = self._map_spacy_entity_type(ent.label_)
                if entity_type:
                    entities.append(Entity(
                        text=ent.text,
                        type=entity_type,
                        start=ent.start_char,
                        end=ent.end_char,
                        confidence=0.9
                    ))

        except Exception as e:
            self.logger.error(f"Entity extraction failed: {e}")

        return entities

    def _extract_entities_regex(self, text: str) -> List[Entity]:
        """Fallback entity extraction using regex."""
        entities = []

        # Extract money amounts
        money_pattern = r'\$[\d,]+(?:\.\d{2})?'
        for match in re.finditer(money_pattern, text):
            entities.append(Entity(
                text=match.group(),
                type=EntityType.MONEY,
                start=match.start(),
                end=match.end(),
                confidence=0.8
            ))

        # Extract dates
        date_pattern = r'\d{1,2}/\d{1,2}/\d{2,4}'
        for match in re.finditer(date_pattern, text):
            entities.append(Entity(
                text=match.group(),
                type=EntityType.DATE,
                start=match.start(),
                end=match.end(),
                confidence=0.7
            ))

        return entities

    def _map_spacy_entity_type(self, spacy_label: str) -> Optional[EntityType]:
        """Map spaCy entity labels to our entity types."""
        mapping = {
            'ORG': EntityType.COMPANY,
            'PERSON': EntityType.PERSON,
            'DATE': EntityType.DATE,
            'MONEY': EntityType.MONEY,
            'GPE': EntityType.LOCATION,
            'LOC': EntityType.LOCATION,
            'QUANTITY': EntityType.QUANTITY,
        }
        return mapping.get(spacy_label)

    def _extract_keywords(self, text: str, top_n: int = 10) -> List[str]:
        """Extract important keywords."""
        if self.nlp is None:
            # Simple fallback: extract capitalized words
            words = re.findall(r'\b[A-Z][a-z]+\b', text)
            return list(set(words))[:top_n]

        try:
            doc = self.nlp(text[:1000000])

            # Extract nouns and proper nouns
            keywords = [
                token.text.lower()
                for token in doc
                if token.pos_ in ['NOUN', 'PROPN'] and not token.is_stop
            ]

            # Count frequency
            from collections import Counter
            freq = Counter(keywords)

            return [word for word, _ in freq.most_common(top_n)]

        except Exception as e:
            self.logger.error(f"Keyword extraction failed: {e}")
            return []

    def _extract_action_items(self, text: str) -> List[str]:
        """Extract action items from text."""
        action_items = []

        # Look for action verbs and patterns
        action_patterns = [
            r'(?:TODO|TO DO):?\s*(.+?)(?:\n|$)',
            r'(?:ACTION|ACTION ITEM):?\s*(.+?)(?:\n|$)',
            r'(?:will|shall|must|should)\s+(.+?)(?:\.|$)',
            r'(?:review|approve|submit|provide|complete)\s+(.+?)(?:\.|$)',
        ]

        for pattern in action_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                action_items.append(match.group(1).strip())

        return action_items[:20]  # Limit to 20 items

    def _extract_key_dates(self, text: str) -> List[Tuple[str, datetime]]:
        """Extract important dates with context."""
        key_dates = []

        # Simple date extraction
        date_pattern = r'(\w+\s+\d{1,2},\s+\d{4}|\d{1,2}/\d{1,2}/\d{2,4})'

        matches = re.finditer(date_pattern, text)
        for match in matches:
            try:
                date_str = match.group(1)
                # Try to parse the date
                # In production, use dateutil.parser
                key_dates.append((date_str, datetime.now()))
            except Exception:
                continue

        return key_dates[:10]  # Limit to 10 dates

    def _generate_summary(self, text: str, max_length: int = 200) -> str:
        """Generate document summary."""
        # Simple extractive summarization: take first few sentences
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 20]

        summary = []
        length = 0

        for sentence in sentences[:5]:
            if length + len(sentence) > max_length:
                break
            summary.append(sentence)
            length += len(sentence)

        return '. '.join(summary) + '.' if summary else text[:max_length]

    def _calculate_confidence(
        self,
        raw_text: str,
        cleaned_text: str,
        entities: List[Entity]
    ) -> float:
        """Calculate processing confidence score."""
        score = 1.0

        # Penalize if text is very short
        if len(cleaned_text) < 100:
            score *= 0.5

        # Penalize if too much text was lost in cleaning
        if len(raw_text) > 0:
            ratio = len(cleaned_text) / len(raw_text)
            if ratio < 0.5:
                score *= 0.7

        # Boost if entities were found
        if len(entities) > 5:
            score = min(1.0, score * 1.1)

        return score


# Singleton instance
_document_ai_service = None


def get_document_ai_service() -> DocumentAIService:
    """Get or create document AI service singleton."""
    global _document_ai_service
    if _document_ai_service is None:
        _document_ai_service = DocumentAIService()
    return _document_ai_service
