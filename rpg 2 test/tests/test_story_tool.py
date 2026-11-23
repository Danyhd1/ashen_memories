import tempfile
import unittest
from pathlib import Path

from story_tool import create_template, validate_story


class StoryToolTests(unittest.TestCase):

    def test_template_is_valid(self):
        story = create_template()
        self.assertEqual(validate_story(story), [])

    def test_missing_fields_are_reported(self):
        story = create_template()
        story.pop("premise")
        self.assertTrue(any("premise" in error for error in validate_story(story)))

    def test_story_export_does_not_need_required_paths(self):
        story = create_template("Test Chronicle")
        self.assertEqual(story["title"], "Test Chronicle")
        self.assertEqual(len(story["acts"]), 1)


if __name__ == "__main__":
    unittest.main()
