import requests
import csv
from datetime import datetime, timedelta
from collections import defaultdict, Counter

class MovieDataProcessor:
    BASE_URL = "https://api.themoviedb.org/3/discover/movie"
    GENRE_URL = "https://api.themoviedb.org/3/genre/movie/list?language=en"

    HEADERS = {
        "accept": "application/json",
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiIzMTI3NGFmYTRlNTUyMjRjYzRlN2Q0NmNlMTNkOTZjOSIsInN1YiI6IjVkNmZhMWZmNzdjMDFmMDAxMDU5NzQ4OSIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.lbpgyXlOXwrbY0mUmP-zQpNAMCw_h-oaudAJB6Cn5c8"
    }

    def __init__(self, pages):
        self.pages = pages
        self.movies = []
        self.original_movies = []
        self.genres_map = {}
        self._fetch_genres()
        self._fetch_movies()

    def _fetch_genres(self):
        response = requests.get(self.GENRE_URL, headers=self.HEADERS)
        data = response.json()
        self.genres_map = {genre['id']: genre['name'] for genre in data['genres']}

    def _fetch_movies(self):
        for page in range(1, self.pages + 1):
            url = f"{self.BASE_URL}?include_adult=false&include_video=false&sort_by=popularity.desc&page={page}"
            response = requests.get(url, headers=self.HEADERS)
            data = response.json()
            self.movies.extend(data['results'])
        self.original_movies = list(self.movies)
        print(f"Loaded {len(self.movies)} movies.")

    def get_all_data(self):
        return self.movies

    def get_indexed_data(self):
        return [self.movies[i] for i in range(3, min(19, len(self.movies)), 4)]

    def get_most_popular_title(self):
        return max(self.movies, key=lambda x: x['popularity'])['title']

    def get_titles_with_keywords(self, *keywords):
        return [
            movie['title'] for movie in self.movies
            if 'overview' in movie and any(keyword.lower() in movie['overview'].lower() for keyword in keywords)
        ]

    def get_unique_genres(self):
        genre_ids = {gid for movie in self.movies for gid in movie.get('genre_ids', [])}
        return frozenset(self.genres_map.get(gid, 'Unknown') for gid in genre_ids)

    def delete_movies_by_genre(self, genre_name):
        genre_id = next((gid for gid, name in self.genres_map.items() if name.lower() == genre_name.lower()), None)
        if genre_id is not None:
            self.movies = [m for m in self.movies if genre_id not in m.get('genre_ids', [])]

    def get_most_popular_genres(self):
        counter = Counter()
        for movie in self.movies:
            for gid in movie.get('genre_ids', []):
                counter[self.genres_map.get(gid, 'Unknown')] += 1
        return dict(counter.most_common())

    def get_grouped_titles_by_genres(self):
        genre_groups = defaultdict(list)
        for movie in self.movies:
            for gid in movie.get('genre_ids', []):
                genre_groups[gid].append(movie['title'])

        pairs = set()
        for titles in genre_groups.values():
            for i in range(0, len(titles) - 1, 2):
                pairs.add((titles[i], titles[i + 1]))
        return frozenset(pairs)

    def get_original_and_modified_data(self):
        modified = [dict(movie) for movie in self.original_movies]
        for movie in modified:
            if movie.get('genre_ids'):
                movie['genre_ids'][0] = 22
        return self.original_movies, modified

    def get_transformed_data(self):
        transformed = []
        for movie in self.movies:
            try:
                title = movie.get('title', 'unknown')
                popularity = round(movie.get('popularity', 0), 1)
                score = int(movie.get('vote_average', 0))
                release_str = movie.get('release_date', '')
                release_date = datetime.strptime(release_str, "%Y-%m-%d") if release_str else datetime.today()
                last_day = release_date + timedelta(weeks=10)
                transformed.append({
                    'title': title,
                    'popularity': popularity,
                    'score': score,
                    'last_day_in_cinema': last_day.strftime('%Y-%m-%d')
                })
            except Exception:
                continue
        return sorted(transformed, key=lambda x: (-x['score'], -x['popularity']))

    def write_transformed_to_csv(self, filepath):
        transformed = self.get_transformed_data()
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['title', 'popularity', 'score', 'last_day_in_cinema'])
            writer.writeheader()
            writer.writerows(transformed)
        print(f"Saved transformed data to {filepath}")

if __name__ == "__main__":
    processor = MovieDataProcessor(pages=3)
    print(processor.get_most_popular_title())
    processor.write_transformed_to_csv("transformed_movies.csv")
