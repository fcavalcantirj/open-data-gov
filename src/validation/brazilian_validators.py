"""
Brazilian Document Validation System
Implements CPF and CNPJ validation algorithms as specified in the architecture document.
"""

import re
from typing import Optional, Union


class BrazilianValidator:
    """
    Validates Brazilian documents (CPF and CNPJ) using official algorithms.
    Based on the architecture specification in initial_archtecture-alfa.md
    """

    @staticmethod
    def validate_cpf(cpf: Union[str, None]) -> bool:
        """
        Validate CPF using Brazilian algorithm with verification digits.

        Args:
            cpf: CPF string with or without formatting

        Returns:
            bool: True if CPF is valid, False otherwise
        """
        if not cpf:
            return False

        # Remove all non-digit characters
        cpf = re.sub(r'[^\d]', '', str(cpf))

        # CPF must have exactly 11 digits
        if len(cpf) != 11:
            return False

        # CPF cannot be all same digits
        if cpf == cpf[0] * 11:
            return False

        # Calculate first verification digit
        sum1 = sum(int(cpf[i]) * (10 - i) for i in range(9))
        digit1 = 11 - (sum1 % 11) if (sum1 % 11) >= 2 else 0

        # Calculate second verification digit
        sum2 = sum(int(cpf[i]) * (11 - i) for i in range(10))
        digit2 = 11 - (sum2 % 11) if (sum2 % 11) >= 2 else 0

        # Verify both digits
        return cpf[9:] == f"{digit1}{digit2}"

    @staticmethod
    def validate_cnpj(cnpj: Union[str, None]) -> bool:
        """
        Validate CNPJ using Brazilian algorithm with verification digits.

        Args:
            cnpj: CNPJ string with or without formatting

        Returns:
            bool: True if CNPJ is valid, False otherwise
        """
        if not cnpj:
            return False

        # Remove all non-digit characters
        cnpj = re.sub(r'[^\d]', '', str(cnpj))

        # CNPJ must have exactly 14 digits
        if len(cnpj) != 14:
            return False

        # Weight arrays for verification digit calculation
        weights1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        weights2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]

        # Calculate first verification digit
        sum1 = sum(int(cnpj[i]) * weights1[i] for i in range(12))
        digit1 = 11 - (sum1 % 11) if (sum1 % 11) >= 2 else 0

        # Calculate second verification digit
        sum2 = sum(int(cnpj[i]) * weights2[i] for i in range(13))
        digit2 = 11 - (sum2 % 11) if (sum2 % 11) >= 2 else 0

        # Verify both digits
        return cnpj[12:] == f"{digit1}{digit2}"

    @staticmethod
    def format_cpf(cpf: str) -> Optional[str]:
        """
        Format CPF with standard Brazilian formatting (XXX.XXX.XXX-XX).

        Args:
            cpf: Raw CPF string

        Returns:
            Formatted CPF string or None if invalid
        """
        if not BrazilianValidator.validate_cpf(cpf):
            return None

        clean_cpf = re.sub(r'[^\d]', '', cpf)
        return f"{clean_cpf[:3]}.{clean_cpf[3:6]}.{clean_cpf[6:9]}-{clean_cpf[9:]}"

    @staticmethod
    def format_cnpj(cnpj: str) -> Optional[str]:
        """
        Format CNPJ with standard Brazilian formatting (XX.XXX.XXX/XXXX-XX).

        Args:
            cnpj: Raw CNPJ string

        Returns:
            Formatted CNPJ string or None if invalid
        """
        if not BrazilianValidator.validate_cnpj(cnpj):
            return None

        clean_cnpj = re.sub(r'[^\d]', '', cnpj)
        return f"{clean_cnpj[:2]}.{clean_cnpj[2:5]}.{clean_cnpj[5:8]}/{clean_cnpj[8:12]}-{clean_cnpj[12:]}"

    @staticmethod
    def clean_document(document: str) -> str:
        """
        Remove all formatting from Brazilian documents.

        Args:
            document: Document string with formatting

        Returns:
            Clean document string with only digits
        """
        return re.sub(r'[^\d]', '', str(document))

    @staticmethod
    def identify_document_type(document: str) -> Optional[str]:
        """
        Identify whether a document is CPF or CNPJ based on length and validation.

        Args:
            document: Document string

        Returns:
            'cpf', 'cnpj', or None if invalid
        """
        clean_doc = BrazilianValidator.clean_document(document)

        if len(clean_doc) == 11 and BrazilianValidator.validate_cpf(clean_doc):
            return 'cpf'
        elif len(clean_doc) == 14 and BrazilianValidator.validate_cnpj(clean_doc):
            return 'cnpj'
        else:
            return None


class DocumentValidationError(Exception):
    """Custom exception for document validation errors."""
    pass


def validate_brazilian_document(document: str, doc_type: str) -> bool:
    """
    Convenience function to validate Brazilian documents with type checking.

    Args:
        document: Document string
        doc_type: 'cpf' or 'cnpj'

    Returns:
        bool: True if valid

    Raises:
        DocumentValidationError: If document type is invalid
    """
    if doc_type.lower() == 'cpf':
        return BrazilianValidator.validate_cpf(document)
    elif doc_type.lower() == 'cnpj':
        return BrazilianValidator.validate_cnpj(document)
    else:
        raise DocumentValidationError(f"Invalid document type: {doc_type}")


if __name__ == "__main__":
    # Test cases for validation
    test_cases = [
        # Valid CPFs
        ("12345678909", "cpf", True),
        ("123.456.789-09", "cpf", True),

        # Invalid CPFs
        ("12345678901", "cpf", False),
        ("11111111111", "cpf", False),
        ("123456789", "cpf", False),

        # Valid CNPJs
        ("11222333000181", "cnpj", True),
        ("11.222.333/0001-81", "cnpj", True),

        # Invalid CNPJs
        ("11222333000182", "cnpj", False),
        ("11111111111111", "cnpj", False),
    ]

    print("Testing Brazilian Document Validation:")
    print("=" * 50)

    for document, doc_type, expected in test_cases:
        if doc_type == "cpf":
            result = BrazilianValidator.validate_cpf(document)
        else:
            result = BrazilianValidator.validate_cnpj(document)

        status = "✓" if result == expected else "✗"
        print(f"{status} {document} ({doc_type}): {result} (expected {expected})")