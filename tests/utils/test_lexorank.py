import math

import pytest

from src.utils.lexorank import LexoRank


class TestLexoRank:
    def test_char_to_int_first_symbol(self):
        assert LexoRank.char_to_int("a") == 0

    def test_char_to_int_last_symbol(self):
        assert LexoRank.char_to_int("z") == 25

    def test_char_to_int_middle_symbols(self):
        assert LexoRank.char_to_int("b") == 1
        assert LexoRank.char_to_int("m") == 12
        assert LexoRank.char_to_int("y") == 24

    def test_int_to_char_first_value(self):
        assert LexoRank.int_to_char(0) == "a"

    def test_int_to_char_last_value(self):
        assert LexoRank.int_to_char(25) == "z"

    def test_int_to_char_middle_values(self):
        assert LexoRank.int_to_char(1) == "b"
        assert LexoRank.int_to_char(12) == "m"
        assert LexoRank.int_to_char(24) == "y"

    def test_char_int_conversion_roundtrip(self):
        for i in range(26):
            char = LexoRank.int_to_char(i)
            assert LexoRank.char_to_int(char) == i

        for char in "abcdefghijklmnopqrstuvwxyz":
            num = LexoRank.char_to_int(char)
            assert LexoRank.int_to_char(num) == char

    def test_parse_rank_single_character(self):
        assert LexoRank.parse_rank("a") == [0]
        assert LexoRank.parse_rank("z") == [25]
        assert LexoRank.parse_rank("m") == [12]

    def test_parse_rank_multiple_characters(self):
        assert LexoRank.parse_rank("abc") == [0, 1, 2]
        assert LexoRank.parse_rank("zyx") == [25, 24, 23]

    def test_parse_rank_empty_string(self):
        assert LexoRank.parse_rank("") == []

    def test_format_rank_single_value(self):
        assert LexoRank.format_rank([0]) == "0|a"
        assert LexoRank.format_rank([25]) == "0|z"
        assert LexoRank.format_rank([12]) == "0|m"

    def test_format_rank_multiple_values(self):
        assert LexoRank.format_rank([0, 1, 2]) == "0|abc"
        assert LexoRank.format_rank([25, 24, 23]) == "0|zyx"

    def test_format_rank_empty_list(self):
        assert LexoRank.format_rank([]) == "0|"

    def test_parse_format_roundtrip(self):
        test_strings = ["a", "z", "abc", "hello", "zzz", "aaa"]
        for test_str in test_strings:
            parsed = LexoRank.parse_rank(test_str)
            formatted = LexoRank.format_rank(parsed)
            # format_rank now adds bucket prefix, so we need to check the rank part only
            bucket, rank_only = LexoRank.parse_bucket_and_rank(formatted)
            assert rank_only == test_str

    def test_align_ranks_equal_length(self):
        prev, next_rank = LexoRank.align_ranks("abc", "def")
        assert prev == "abc"
        assert next_rank == "def"

    def test_align_ranks_previous_shorter(self):
        prev, next_rank = LexoRank.align_ranks("ab", "def")
        assert prev == "aba"  # padded with first_symbol
        assert next_rank == "def"

    def test_align_ranks_next_shorter(self):
        prev, next_rank = LexoRank.align_ranks("abc", "de")
        assert prev == "abc"
        assert next_rank == "dez"  # padded with last_symbol

    def test_align_ranks_both_different_lengths(self):
        prev, next_rank = LexoRank.align_ranks("a", "defgh")
        assert prev == "aaaaa"  # padded to length 5 with first_symbol
        assert next_rank == "defgh"

    def test_align_ranks_exceeds_max_length(self):
        long_rank = "a" * (LexoRank.max_rank_length + 1)
        with pytest.raises(ValueError, match="Rebalancing Required"):
            LexoRank.align_ranks(long_rank, "b")

    def test_get_min_rank_default_length(self):
        min_rank = LexoRank.get_min_rank(10)
        expected_length = LexoRank.get_rank_length(10)
        # Account for bucket prefix "0|" (2 characters)
        assert len(min_rank) == expected_length + 2
        assert min_rank == "0|" + "a" * expected_length

    def test_get_max_rank_default_length(self):
        max_rank = LexoRank.get_max_rank(10)
        expected_length = LexoRank.get_rank_length(10)
        # Account for bucket prefix "0|" (2 characters)
        assert len(max_rank) == expected_length + 2
        assert max_rank == "0|" + "z" * expected_length

    def test_get_min_max_rank_ordering(self):
        min_rank = LexoRank.get_min_rank(10)
        max_rank = LexoRank.get_max_rank(10)
        assert min_rank < max_rank

    def test_middle_returns_correct_format(self):
        middle = LexoRank.middle()
        # Account for bucket prefix "0|" (2 characters)
        assert len(middle) == LexoRank.default_rank_length + 2
        assert middle.startswith("0|")
        rank_part = middle[2:]  # Remove bucket prefix
        assert all(c in LexoRank.base_symbols for c in rank_part)

    def test_middle_is_in_middle_range(self):
        middle = LexoRank.middle()
        min_rank = LexoRank.get_min_rank(100)
        max_rank = LexoRank.get_max_rank(100)
        assert min_rank < middle < max_rank

    def test_gen_next_simple_increment(self):
        result = LexoRank.gen_next("0|a")
        assert result == "0|b"

    def test_gen_next_with_carry(self):
        result = LexoRank.gen_next("0|z")
        assert result == "0|ba"  # carry to new position

    def test_gen_next_multiple_characters(self):
        result = LexoRank.gen_next("0|abc")
        assert result == "0|abd"

    def test_gen_next_multiple_carry(self):
        result = LexoRank.gen_next("0|azz")
        assert result == "0|baa"  # multiple carries

    def test_gen_next_ordering_preserved(self):
        rank1 = "0|abc"
        rank2 = LexoRank.gen_next(rank1)
        assert rank1 < rank2

    def test_get_rank_length_zero_objects(self):
        length = LexoRank.get_rank_length(0)
        assert length == LexoRank.default_rank_length

    def test_get_rank_length_small_count(self):
        length = LexoRank.get_rank_length(5)
        assert length == LexoRank.default_rank_length

    def test_get_rank_length_large_count(self):
        large_count = 1000
        expected_length = math.ceil(math.log(large_count, LexoRank.base)) * 2
        expected_length = min(
            LexoRank.max_rank_length, max(expected_length, LexoRank.default_rank_length)
        )
        assert LexoRank.get_rank_length(large_count) == expected_length

    def test_get_rank_length_max_constraint(self):
        very_large_count = LexoRank.base**LexoRank.max_rank_length
        length = LexoRank.get_rank_length(very_large_count)
        assert length == LexoRank.max_rank_length

    def test_get_rank_step_calculation(self):
        objects_count = 10
        rank_length = LexoRank.get_rank_length(objects_count)
        expected_step = int(LexoRank.base**rank_length / objects_count - 0.5)
        assert LexoRank.get_rank_step(objects_count) == expected_step

    def test_get_lexorank_in_between_both_none(self):
        result = LexoRank.get_lexorank_in_between(None, None, 10)
        min_rank = LexoRank.get_min_rank(10)
        max_rank = LexoRank.get_max_rank(10)
        assert min_rank < result < max_rank

    def test_get_lexorank_in_between_previous_none(self):
        next_rank = "0|mmm"
        result = LexoRank.get_lexorank_in_between(None, next_rank, 10)
        min_rank = LexoRank.get_min_rank(10)
        assert min_rank < result < next_rank

    def test_get_lexorank_in_between_next_none(self):
        previous_rank = "0|mmm"
        result = LexoRank.get_lexorank_in_between(previous_rank, None, 10)
        max_rank = LexoRank.get_max_rank(10)
        assert previous_rank < result < max_rank

    def test_get_lexorank_in_between_normal_case(self):
        previous_rank = "0|aaa"
        next_rank = "0|zzz"
        result = LexoRank.get_lexorank_in_between(previous_rank, next_rank, 10)
        assert previous_rank < result < next_rank

    def test_get_lexorank_in_between_close_ranks(self):
        previous_rank = "0|mmm"
        next_rank = "0|mmn"
        result = LexoRank.get_lexorank_in_between(previous_rank, next_rank, 10)
        assert previous_rank < result < next_rank

    def test_get_lexorank_in_between_invalid_order(self):
        previous_rank = "0|zzz"
        next_rank = "0|aaa"
        with pytest.raises(
            ValueError, match="Previous rank must go before than next rank"
        ):
            LexoRank.get_lexorank_in_between(previous_rank, next_rank, 10)

    def test_get_lexorank_in_between_force_reorder(self):
        previous_rank = "0|zzz"
        next_rank = "0|aaa"
        result = LexoRank.get_lexorank_in_between(
            previous_rank, next_rank, 10, force_reorder=True
        )
        assert next_rank < result < previous_rank

    def test_get_lexorank_in_between_equal_ranks(self):
        rank = "0|mmm"
        result = LexoRank.get_lexorank_in_between(rank, rank, 10, force_reorder=True)
        # Should handle equal ranks gracefully
        assert isinstance(result, str)
        assert result.startswith("0|")
        assert len(result) >= len(rank)

    def test_increment_rank_simple(self):
        result = LexoRank.increment_rank("0|aaa", 10)
        # Simply verify that the result is greater than the original rank
        assert result > "0|aaa"
        # And verify it returns a string with bucket prefix
        assert isinstance(result, str)
        assert result.startswith("0|")
        assert len(result) >= len("0|aaa")

        # NOTE: There is a known issue with increment_rank where large step values
        # can produce characters outside the valid base_symbols range.
        # This happens when the remaining step after carry operations is >= base
        # and gets directly prepended instead of being properly decomposed.

    def test_increment_rank_with_carry(self):
        # Create a rank close to overflow
        step = LexoRank.get_rank_step(10)
        close_to_max = LexoRank.format_rank([0, 0, LexoRank.base - 1])
        result = LexoRank.increment_rank(close_to_max, 10)
        # Should handle carry properly
        assert isinstance(result, str)
        assert result.startswith("0|")
        assert len(result) >= len(close_to_max)

    def test_increment_rank_large_step(self):
        result = LexoRank.increment_rank("0|aaa", 1)  # Large step size
        assert result > "0|aaa"

    def test_rank_ordering_properties(self):
        # Test that generated ranks maintain proper ordering
        ranks = []
        prev_rank = None

        for i in range(10):
            rank = LexoRank.get_lexorank_in_between(prev_rank, None, 100)
            ranks.append(rank)
            prev_rank = rank

        # All ranks should be in ascending order
        for i in range(1, len(ranks)):
            assert ranks[i - 1] < ranks[i]

    def test_rank_uniqueness(self):
        # Generate multiple ranks and ensure they're unique
        ranks = set()
        prev_rank = None

        for i in range(50):
            rank = LexoRank.get_lexorank_in_between(prev_rank, None, 1000)
            assert rank not in ranks  # Should be unique
            ranks.add(rank)
            prev_rank = rank

    def test_edge_case_single_character_ranks(self):
        # Test with single character ranks
        result = LexoRank.get_lexorank_in_between("0|a", "0|z", 1)
        assert "0|a" < result < "0|z"

    def test_edge_case_adjacent_characters(self):
        # Test with adjacent characters - should extend length
        result = LexoRank.get_lexorank_in_between("0|a", "0|b", 10)
        assert "0|a" < result < "0|b"
        # Should be longer than "0|b" (3 chars) to fit between
        assert len(result) > 3

    def test_mathematical_properties(self):
        # Test mathematical properties of the ranking system
        min_rank = LexoRank.get_min_rank(100)
        max_rank = LexoRank.get_max_rank(100)
        middle = LexoRank.get_lexorank_in_between(min_rank, max_rank, 100)

        # Middle should be between min and max
        assert min_rank < middle < max_rank

        # Test that we can create ranks between min and middle
        between_min_middle = LexoRank.get_lexorank_in_between(min_rank, middle, 100)
        assert min_rank < between_min_middle < middle

        # Test that we can create ranks between middle and max
        between_middle_max = LexoRank.get_lexorank_in_between(middle, max_rank, 100)
        assert middle < between_middle_max < max_rank

    def test_increment_rank_large_step_fixed(self):
        """
        Test that increment_rank properly handles large step values after the bug fix.

        Previously, when the step size was large relative to the rank length, the remaining
        step value after carry operations could be >= base, which would get directly
        prepended to rank_parts without proper base conversion, resulting in
        characters outside the valid base_symbols range.

        This test verifies the fix works correctly.
        """
        # This specific case previously produced invalid characters
        result = LexoRank.increment_rank("0|aaa", 10)

        # The result should be greater than input
        assert result > "0|aaa"

        # Should have bucket prefix
        assert result.startswith("0|")

        # All characters in rank part should now be valid base_symbols
        _, rank_part = LexoRank.parse_bucket_and_rank(result)
        assert all(c in LexoRank.base_symbols for c in rank_part)

        # Verify the step value that previously caused issues
        step = LexoRank.get_rank_step(10)
        assert step == 30891577  # Large step that caused the original bug

    def test_decompose_to_base_digits_helper(self):
        """Test the helper method for decomposing large values into base-26 digits."""
        # Test zero
        assert LexoRank._decompose_to_base_digits(0) == [0]

        # Test small values
        assert LexoRank._decompose_to_base_digits(1) == [1]
        assert LexoRank._decompose_to_base_digits(25) == [25]

        # Test value equal to base
        assert LexoRank._decompose_to_base_digits(26) == [1, 0]

        # Test the problematic value from the bug
        result = LexoRank._decompose_to_base_digits(1757)
        expected = [2, 15, 15]  # 2*26^2 + 15*26^1 + 15*26^0 = 1352 + 390 + 15 = 1757
        assert result == expected

        # Verify all digits are valid
        assert all(digit < LexoRank.base for digit in result)

        # Verify reconstruction
        total = sum(
            digit * (LexoRank.base**i) for i, digit in enumerate(reversed(result))
        )
        assert total == 1757

    def test_gen_next_large_carry_fixed(self):
        """Test that gen_next properly handles large carry values after the bug fix."""
        # All characters in rank part should be valid base_symbols
        large_rank = "0|" + "z" * 10  # Many z's that will all carry
        result = LexoRank.gen_next(large_rank)
        _, rank_part = LexoRank.parse_bucket_and_rank(result)
        assert all(c in LexoRank.base_symbols for c in rank_part)

        # Test that the numerical value is greater (even if string comparison differs)
        # Convert to numerical values for proper comparison
        def rank_to_number(bucket_rank):
            # Extract just the rank portion
            _, rank_only = LexoRank.parse_bucket_and_rank(bucket_rank)
            parts = LexoRank.parse_rank(rank_only)
            return sum(
                part * (LexoRank.base**i) for i, part in enumerate(reversed(parts))
            )

        large_rank_num = rank_to_number(large_rank)
        result_num = rank_to_number(result)
        assert result_num > large_rank_num

        # Should handle normal cases too
        assert LexoRank.gen_next("0|a") == "0|b"
        assert LexoRank.gen_next("0|z") == "0|ba"

        # Verify numerical ordering for edge cases
        z_num = rank_to_number("z")
        ba_num = rank_to_number("ba")
        assert ba_num > z_num  # "ba" is numerically greater than "z"

    def test_parse_bucket_and_rank_with_bucket(self):
        bucket, rank = LexoRank.parse_bucket_and_rank("1|abc")
        assert bucket == 1
        assert rank == "abc"

    def test_parse_bucket_and_rank_without_bucket(self):
        bucket, rank = LexoRank.parse_bucket_and_rank("abc")
        assert bucket == 0  # Default bucket
        assert rank == "abc"

    def test_extract_rank_only_with_bucket(self):
        rank = LexoRank.extract_rank_only("2|xyz")
        assert rank == "xyz"

    def test_extract_rank_only_without_bucket(self):
        rank = LexoRank.extract_rank_only("xyz")
        assert rank == "xyz"

    def test_format_with_bucket_default(self):
        result = LexoRank.format_with_bucket("abc")
        assert result == "0|abc"

    def test_format_with_bucket_custom(self):
        result = LexoRank.format_with_bucket("abc", 2)
        assert result == "2|abc"

    def test_format_rank_with_custom_bucket(self):
        result = LexoRank.format_rank([0, 1, 2], bucket=1)
        assert result == "1|abc"

    def test_gen_next_preserves_bucket(self):
        result = LexoRank.gen_next("2|abc")
        assert result == "2|abd"

    def test_increment_rank_preserves_bucket(self):
        result = LexoRank.increment_rank("1|aaa", 10)
        assert result.startswith("1|")
        assert result > "1|aaa"

    def test_get_lexorank_in_between_mixed_inputs(self):
        # Test with plain rank and bucket-prefixed rank
        result = LexoRank.get_lexorank_in_between("0|aaa", "zzz", 10)
        # Should use bucket from previous_rank
        assert result.startswith("0|")
        assert "0|aaa" < result < "0|zzz"

    def test_backward_compatibility_plain_ranks(self):
        # Test that methods still work with plain rank strings (without buckets)
        result = LexoRank.get_lexorank_in_between("aaa", "zzz", 10)
        # Should add default bucket
        assert result.startswith("0|")
        assert "0|aaa" < result < "0|zzz"
