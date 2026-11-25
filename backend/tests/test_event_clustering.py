import unittest

from backend.main import build_event_clusters


class EventClusteringRegressionTests(unittest.TestCase):
    def setUp(self):
        self.articles = [
            {
                "id": 101,
                "source": "BBC",
                "title": "Trump to meet Chinese leader Xi Jinping and Russia's Vladimir Putin for joint summit",
                "published": "Mon, 16 Nov 2026 09:00:00 GMT",
                "countries": "China, United States, Russia",
                "topics": "Diplomacy",
            },
            {
                "id": 102,
                "source": "NPR",
                "title": "Trump Putin and Xi plan historic joint meeting in China next week",
                "published": "Tue, 17 Nov 2026 09:00:00 GMT",
                "countries": "China, United States, Russia",
                "topics": "Diplomacy",
            },
            {
                "id": 103,
                "source": "France24",
                "title": "Trump and Xi Jinping prepare for China summit with Putin",
                "published": "Tue, 17 Nov 2026 11:00:00 GMT",
                "countries": "China, United States, Russia",
                "topics": "Diplomacy",
            },
            {
                "id": 104,
                "source": "Euronews",
                "title": "China says no information on whether North Korea's leader Kim will meet Trump",
                "published": "Mon, 16 Nov 2026 12:00:00 GMT",
                "countries": "China, North Korea, United States",
                "topics": "Diplomacy",
            },
        ]

    def test_trump_kim_story_is_not_joined_to_xi_putin_summit(self):
        result = build_event_clusters(
            self.articles,
            window_days=30,
            min_articles=2,
        )

        self.assertEqual(result["cluster_count"], 1)
        summit_cluster = result["clusters"][0]
        self.assertEqual(summit_cluster["article_count"], 3)

        clustered_ids = {
            article["id"] for article in summit_cluster["articles"]
        }
        self.assertEqual(clustered_ids, {101, 102, 103})
        self.assertNotIn(104, clustered_ids)

    def test_related_summit_reports_still_cluster_together(self):
        result = build_event_clusters(
            self.articles[:3],
            window_days=30,
            min_articles=2,
        )

        self.assertEqual(result["cluster_count"], 1)
        self.assertEqual(result["clusters"][0]["article_count"], 3)


if __name__ == "__main__":
    unittest.main()
