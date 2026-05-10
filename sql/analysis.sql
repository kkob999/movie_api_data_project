-- 1. Top 10 movies by popularity score
SELECT title, rating, vote_count, popularity_score, rating_tier, source_list
FROM movies
ORDER BY popularity_score DESC
LIMIT 10;

-- 2. Genre ranking — which genres appear most
SELECT mg.genre_name, COUNT(*) as movie_count
FROM movie_genres mg
JOIN movies m ON mg.tmdb_id = m.tmdb_id
GROUP BY mg.genre_name
ORDER BY movie_count DESC;

-- 3. Average rating by decade
SELECT decade, COUNT(*) as movie_count, ROUND(AVG(rating)::numeric, 2) as avg_rating
FROM movies
WHERE decade != 'Unknown'
GROUP BY decade
ORDER BY decade;

-- 4. Movies in both popular and top_rated lists
SELECT title, rating, vote_count, popularity_score, decade
FROM movies
WHERE source_list = 'both'
ORDER BY popularity_score DESC;

-- 5. Rating tier distribution by source list
SELECT source_list, rating_tier, COUNT(*) as count
FROM movies
GROUP BY source_list, rating_tier
ORDER BY source_list, count DESC;

-- 6. Top genres in popular vs top_rated
SELECT mg.genre_name, m.source_list, COUNT(*) as count
FROM movie_genres mg
JOIN movies m ON mg.tmdb_id = m.tmdb_id
WHERE m.source_list IN ('popular', 'top_rated')
GROUP BY mg.genre_name, m.source_list
ORDER BY count DESC
LIMIT 20;

-- 7. Language diversity — how many non-English movies
SELECT
    CASE WHEN language = 'en' THEN 'English' ELSE 'Non-English' END as language_group,
    COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) as percentage
FROM movies
GROUP BY language_group;