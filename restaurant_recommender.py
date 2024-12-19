# -*- coding: utf-8 -*-
"""restaurant_recommender

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1npzXwlUIugN-MwHnIgakDbts0_X7X4Kn
"""

pip install scikit-learn-extra

!pip install umap-learn

pip install prettytable

import pandas as pd
import numpy as np
from sklearn.cluster import KMeans, DBSCAN
from sklearn_extra.cluster import KMedoids
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import silhouette_score
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
from umap import UMAP

df = pd.read_csv("/content/restaurant_data_correct_names.csv")
print(df.columns)

# --- Define Features ---
features = ['Location', 'City', 'Cuisine', 'Rating', 'Total Reviews', 'Average Cost for Two (INR)']

# --- Preprocessing ---
preprocessor = ColumnTransformer(
    transformers=[
        ('num', StandardScaler(), ['Rating', 'Total Reviews', 'Average Cost for Two (INR)']),
        ('cat', OneHotEncoder(), ['Location', 'City', 'Cuisine'])
    ])

pipeline = Pipeline(steps=[
    ('preprocessor', preprocessor)
])

df_scaled = pipeline.fit_transform(df[features])

# --- PCA for Dimensionality Reduction ---
pca = PCA(n_components=2, random_state=42)
df_pca = pca.fit_transform(df_scaled)

# --- UMAP for Visualization ---
umap = UMAP(n_components=2, random_state=42)
df_umap = umap.fit_transform(df_scaled)

# --- K-Means Clustering ---
kmeans_scores = []
kmeans_inertia = []
k_values = range(2, 11)

for k in k_values:
    kmeans = KMeans(n_clusters=k, random_state=42)
    labels = kmeans.fit_predict(df_pca)  # Using PCA-transformed data
    kmeans_scores.append(silhouette_score(df_pca, labels))
    kmeans_inertia.append(kmeans.inertia_)

# --- DBSCAN Clustering ---
dbscan_scores = []
dbscan_params = []
eps_values = np.arange(0.1, 1.0, 0.1)
min_samples_values = range(2, 10)

for eps in eps_values:
    for min_samples in min_samples_values:
        dbscan = DBSCAN(eps=eps, min_samples=min_samples)
        labels = dbscan.fit_predict(df_pca)
        if len(set(labels)) > 1:  # Ignore noise-only or single-cluster results
            score = silhouette_score(df_pca, labels)
            dbscan_scores.append(score)
            dbscan_params.append((eps, min_samples))

# Best DBSCAN Parameters
if dbscan_scores:
    best_dbscan_idx = np.argmax(dbscan_scores)
    best_dbscan_params = dbscan_params[best_dbscan_idx]
else:
    best_dbscan_params = None

# --- K-Medoids Clustering ---
kmedoids_scores = []
for k in k_values:
    kmedoids = KMedoids(n_clusters=k, random_state=42)
    labels = kmedoids.fit_predict(df_pca)  # Using PCA-transformed data
    kmedoids_scores.append(silhouette_score(df_pca, labels))

# --- Visualization ---

# Elbow Method and Silhouette Scores for K-Means
plt.figure(figsize=(16, 8))

plt.subplot(2, 2, 1)
plt.plot(k_values, kmeans_inertia, marker='o', color='blue', label='Inertia')
plt.xlabel('Number of Clusters (k)')
plt.ylabel('Inertia')
plt.title('K-Means: Elbow Method')
plt.grid(True)
plt.legend()

plt.subplot(2, 2, 2)
plt.plot(k_values, kmeans_scores, marker='o', color='orange', label='Silhouette Score')
plt.xlabel('Number of Clusters (k)')
plt.ylabel('Silhouette Score')
plt.title('K-Means: Silhouette Scores')
plt.grid(True)
plt.legend()

# Silhouette Scores for DBSCAN
plt.subplot(2, 2, 3)
if dbscan_scores:
    plt.scatter(range(len(dbscan_scores)), dbscan_scores, color='green', label='DBSCAN Scores')
    plt.xlabel('Parameter Combinations')
    plt.ylabel('Silhouette Score')
    plt.title('DBSCAN: Silhouette Scores')
    plt.legend()
else:
    plt.text(0.5, 0.5, 'No valid DBSCAN clusters', ha='center')

# Silhouette Scores for K-Medoids
plt.subplot(2, 2, 4)
plt.plot(k_values, kmedoids_scores, marker='o', color='purple', label='K-Medoids')
plt.xlabel('Number of Clusters (k)')
plt.ylabel('Silhouette Score')
plt.title('K-Medoids: Silhouette Scores')
plt.grid(True)
plt.legend()

plt.tight_layout()
plt.show()

# --- Results ---
print("Best K-Means Silhouette Score:", max(kmeans_scores))
print("Optimal Number of Clusters (k) for K-Means:", k_values[np.argmax(kmeans_scores)])
if dbscan_scores:
    print("Best DBSCAN Silhouette Score:", max(dbscan_scores))
    print("Best DBSCAN Parameters (eps, min_samples):", best_dbscan_params)
else:
    print("DBSCAN could not find valid clusters.")
print("Best K-Medoids Silhouette Score:", max(kmedoids_scores))
print("Optimal Number of Clusters (k) for K-Medoids:", k_values[np.argmax(kmedoids_scores)])

from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

# Select features for clustering
features = ['Rating', 'Average Cost for Two (INR)', 'Total Reviews']
scaler = StandardScaler()
scaled_features = scaler.fit_transform(df[features])

# Fit K-Means
kmeans = KMeans(n_clusters=3, random_state=42)  # Adjust `n_clusters` as needed
df['Cluster'] = kmeans.fit_predict(scaled_features)


# Function to recommend restaurants based on city, rating, and price constraints
def recommend_restaurants_by_city_and_constraints(user_city, min_rating, max_price, user_cluster=None):
    user_city = user_city.lower()

    # Check if the entered city exists in the dataset
    available_cities = df['City'].str.lower().unique()
    if user_city not in available_cities:
        print(f"Sorry, we couldn't find any restaurants in the city '{user_city}'.")
        return pd.DataFrame()

    # Filter restaurants in the specified city
    city_restaurants = df[df['City'].str.lower() == user_city]

    # Apply cluster filtering if user_cluster is specified
    if user_cluster is not None:
        city_restaurants = city_restaurants[city_restaurants['Cluster'] == user_cluster]

    # Apply rating and price constraints
    filtered_restaurants = city_restaurants[
        (city_restaurants['Rating'] >= min_rating) &
        (city_restaurants['Average Cost for Two (INR)'] <= max_price)
    ]

    return filtered_restaurants


# Get user input for city, rating, and price
user_city = input("Enter the city: ").strip()
min_rating = float(input("Enter minimum rating (e.g., 4.0): "))
max_price = float(input("Enter maximum price for two (e.g., 1000): "))

# Recommend restaurants based on city, rating, and price constraints
recommended_restaurants = recommend_restaurants_by_city_and_constraints(user_city, min_rating, max_price)

# Display the recommended restaurants using PrettyTable if there are results
if recommended_restaurants.empty:
    print("No restaurants found with the specified criteria.")
else:
    # Create a PrettyTable object to display the output in a tabular format
    table = PrettyTable()
    table.field_names = ["Location","Name", "City", "Cuisine", "Rating", "Total Reviews", "Average Cost for Two (INR)"]

    # Add rows to the table
    for _, row in recommended_restaurants.iterrows():
        table.add_row([row['Location'],row['Name'], row['City'], row['Cuisine'], row['Rating'], row['Total Reviews'], row['Average Cost for Two (INR)']])

    # Print the table
    print(f"\nRecommended Restaurants in {user_city.capitalize()} with rating >= {min_rating} and price <= {max_price}:")
    print(table)