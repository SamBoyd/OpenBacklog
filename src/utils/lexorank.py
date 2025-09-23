#######
## This file is taken for the "django-lexorank/django_lexorank" project
## See https://github.com/rozumdev/django-lexorank/blob/master/django_lexorank/lexorank.py
#######

import math
import string
from typing import List, Optional, Tuple


class LexoRank:
    default_rank_length = 6
    rebalancing_length = 128
    max_rank_length = 200
    base_symbols = string.ascii_lowercase
    first_symbol = base_symbols[0]
    last_symbol = base_symbols[-1]
    base = len(base_symbols)

    # Bucket constants
    DEFAULT_BUCKET = 0
    BUCKET_SEPARATOR = "|"

    @classmethod
    def parse_bucket_and_rank(cls, bucket_rank: str) -> Tuple[int, str]:
        """
        Parse a bucket-prefixed rank string into bucket and rank components.

        Args:
            bucket_rank: String in format '{bucket}|{rank}' or just '{rank}'

        Returns:
            Tuple of (bucket, rank) where bucket is int and rank is string
        """
        if cls.BUCKET_SEPARATOR in bucket_rank:
            bucket_str, rank = bucket_rank.split(cls.BUCKET_SEPARATOR, 1)
            return int(bucket_str), rank
        else:
            # No bucket prefix, assume default bucket
            return cls.DEFAULT_BUCKET, bucket_rank

    @classmethod
    def extract_rank_only(cls, bucket_rank: str) -> str:
        """
        Extract only the rank portion from a bucket-prefixed string.

        Args:
            bucket_rank: String in format '{bucket}|{rank}' or just '{rank}'

        Returns:
            Just the rank portion as string
        """
        _, rank = cls.parse_bucket_and_rank(bucket_rank)
        return rank

    @classmethod
    def format_with_bucket(cls, rank: str, bucket: int = None) -> str:
        """
        Format a rank string with bucket prefix.

        Args:
            rank: The rank string
            bucket: The bucket number (defaults to DEFAULT_BUCKET)

        Returns:
            String in format '{bucket}|{rank}'
        """
        if bucket is None:
            bucket = cls.DEFAULT_BUCKET
        return f"{bucket}{cls.BUCKET_SEPARATOR}{rank}"

    @classmethod
    def char_to_int(cls, char: str) -> int:
        return ord(char) - ord(cls.first_symbol)

    @classmethod
    def int_to_char(cls, num: int) -> str:
        return chr(num + ord(cls.first_symbol))

    @classmethod
    def parse_rank(cls, rank: str) -> List[int]:
        return [cls.char_to_int(char) for char in rank]

    @classmethod
    def format_rank(cls, rank: List[int], bucket: int = None) -> str:
        """
        Format a list of integers into a bucket-prefixed rank string.

        Args:
            rank: List of integers representing the rank
            bucket: The bucket number (defaults to DEFAULT_BUCKET)

        Returns:
            String in format '{bucket}|{rank}'
        """
        rank_string = "".join(map(cls.int_to_char, rank))
        return cls.format_with_bucket(rank_string, bucket)

    @classmethod
    def align_ranks(cls, previous_rank: str, next_rank: str) -> Tuple[str, str]:
        # Extract rank-only portions for alignment
        prev_rank_only = cls.extract_rank_only(previous_rank)
        next_rank_only = cls.extract_rank_only(next_rank)

        max_len = max(len(prev_rank_only), len(next_rank_only))

        if max_len > cls.max_rank_length:
            raise ValueError("Rebalancing Required")

        prev_rank_only = prev_rank_only.ljust(max_len, cls.first_symbol)
        next_rank_only = next_rank_only.ljust(max_len, cls.last_symbol)

        return prev_rank_only, next_rank_only

    @classmethod
    def get_lexorank_in_between(
        cls,
        previous_rank: Optional[str],
        next_rank: Optional[str],
        objects_count: int,
        force_reorder: bool = False,
    ) -> str:
        # Determine the bucket to use (from previous_rank if available, otherwise next_rank, otherwise default)
        bucket = cls.DEFAULT_BUCKET
        if previous_rank:
            bucket, _ = cls.parse_bucket_and_rank(previous_rank)
        elif next_rank:
            bucket, _ = cls.parse_bucket_and_rank(next_rank)

        if not previous_rank:
            previous_rank = cls.get_min_rank(objects_count=objects_count)

        if not next_rank:
            next_rank = cls.get_max_rank(objects_count=objects_count)

        previous_rank_only, next_rank_only = cls.align_ranks(previous_rank, next_rank)

        if force_reorder:
            previous_rank_only, next_rank_only = sorted(
                [previous_rank_only, next_rank_only]
            )
        else:
            if not previous_rank_only < next_rank_only:
                raise ValueError("Previous rank must go before than next rank.")

        previous_rank_parts = cls.parse_rank(previous_rank_only)
        next_rank_parts = cls.parse_rank(next_rank_only)

        total_diff = 0
        for i, previous_rank_part in enumerate(reversed(previous_rank_parts)):
            next_rank_part = next_rank_parts[len(next_rank_parts) - (i + 1)]
            if next_rank_part < previous_rank_part:
                next_rank_part += cls.base
                next_rank_parts[len(next_rank_parts) - (i + 1)] = next_rank_part
                next_rank_parts[len(next_rank_parts) - (i + 2)] -= 1

            diff = next_rank_part - previous_rank_part
            total_diff += diff * (cls.base**i)

        middle_rank_parts = []  # type: ignore[var-annotated]

        offset = 0
        for i, previous_rank_part in enumerate(reversed(previous_rank_parts)):
            to_add = total_diff / 2 / cls.base**i % cls.base
            middle_rank_part = previous_rank_part + to_add + offset
            offset = 0

            if middle_rank_part > cls.base:
                offset = 1
                middle_rank_part -= cls.base

            middle_rank_parts.insert(0, math.floor(middle_rank_part))

        if offset:
            middle_rank_parts.insert(0, cls.char_to_int(cls.first_symbol))

        if middle_rank_parts == previous_rank_parts:
            middle_rank_parts.append(
                (cls.char_to_int(cls.last_symbol) - cls.char_to_int(cls.first_symbol))
                // 2
            )

        return cls.format_rank(middle_rank_parts, bucket)

    @classmethod
    def get_min_rank(cls, objects_count: int) -> str:
        rank_length = cls.get_rank_length(objects_count)
        return cls.format_rank([0] * rank_length)

    @classmethod
    def get_max_rank(cls, objects_count: int) -> str:
        rank_length = cls.get_rank_length(objects_count)
        return cls.format_rank([cls.char_to_int(cls.last_symbol)] * rank_length)

    @classmethod
    def get_rank_step(cls, objects_count: int) -> int:
        rank_length = cls.get_rank_length(objects_count=objects_count)
        return int(cls.base**rank_length / objects_count - 0.5)

    @classmethod
    def get_rank_length(cls, objects_count: int) -> int:
        if objects_count == 0:
            length_required_to_place_all_objects = 1
        else:
            length_required_to_place_all_objects = math.ceil(
                math.log(objects_count, cls.base)
            )
        return min(
            cls.max_rank_length,
            max(length_required_to_place_all_objects * 2, cls.default_rank_length),
        )

    @classmethod
    def _decompose_to_base_digits(cls, value: int) -> List[int]:
        """
        Decompose a large integer value into valid base-26 digits.

        Args:
            value: Integer value to decompose (must be positive)

        Returns:
            List of integers where each integer is < base (26)
        """
        if value == 0:
            return [0]

        digits = []
        while value > 0:
            digits.append(value % cls.base)
            value = value // cls.base

        digits.reverse()
        return digits

    @classmethod
    def increment_rank(cls, rank: str, objects_count: int) -> str:
        # Parse bucket and rank
        bucket, rank_only = cls.parse_bucket_and_rank(rank)
        step = cls.get_rank_step(objects_count=objects_count)
        rank_parts = cls.parse_rank(rank_only)

        for i in range(len(rank_parts) - 1, -1, -1):
            if step == 0:
                break

            total = rank_parts[i] + step
            rank_parts[i] = total % cls.base
            step = total // cls.base

        if step > 0:
            # Properly decompose the remaining step into base-26 digits
            step_digits = cls._decompose_to_base_digits(step)
            rank_parts = step_digits + rank_parts

        return cls.format_rank(rank_parts, bucket)

    @classmethod
    def middle(cls) -> str:
        """Return middle position rank string."""
        # Use default rank length and create middle position
        rank_length = cls.default_rank_length
        middle_value = cls.base // 2
        rank_parts = [middle_value] * rank_length
        return cls.format_rank(rank_parts)

    @classmethod
    def gen_next(cls, rank: str) -> str:
        """Generate next rank position from given rank."""
        # Parse bucket and rank
        bucket, rank_only = cls.parse_bucket_and_rank(rank)
        rank_parts = cls.parse_rank(rank_only)

        # Add 1 to the last position
        carry = 1
        for i in range(len(rank_parts) - 1, -1, -1):
            total = rank_parts[i] + carry
            rank_parts[i] = total % cls.base
            carry = total // LexoRank.base
            if carry == 0:
                break

        # If there's still a carry, properly decompose it into base-26 digits
        if carry > 0:
            carry_digits = cls._decompose_to_base_digits(carry)
            rank_parts = carry_digits + rank_parts

        return cls.format_rank(rank_parts, bucket)
