from flask import Flask, request, jsonify
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import psycopg2
app = Flask(__name__)
hostname = 'localhost'
database = 'quanlycuahang1'
username = 'postgres'
pwd = '24112001'
port_id = 5432
conn = None
cur = None
# Sample data: User-Item Interaction Matrix
# data = {
#     'userId': [ 1,   1,   1,   2,   2,   3,   3,   4],
#     'itemId': ['A', 'B', 'C', 'A', 'C', 'B', 'D', 'C']
# }


def get_user_recommendations(target_user_id, num_recommendations=3, data = {},interactions_df = None ,user_item_matrix = None):
    # interactions_df = pd.DataFrame(data)

    # # Create a User-Item Matrix
    # user_item_matrix = interactions_df.pivot_table(index='userId', columns='itemId', aggfunc='size', fill_value=0)

    # Compute Cosine Similarity between users
    user_similarity = cosine_similarity(user_item_matrix)
    user_similarity_df = pd.DataFrame(user_similarity, index=user_item_matrix.index, columns=user_item_matrix.index)

    # Get similar users
    similar_users = user_similarity_df[target_user_id].sort_values(ascending=False)
    similar_users = similar_users[similar_users.index != target_user_id]  # Exclude the target user

    # Find items interacted by similar users that the target user has not interacted
    user_interacted_items = user_item_matrix.loc[target_user_id]
    user_interacted_items = user_interacted_items[user_interacted_items > 0].index

    recommendations = {}
    for user_id, similarity in similar_users.items():
        user_interactions = user_item_matrix.loc[user_id]
        for item in user_interactions.index:
            if item not in user_interacted_items and user_interactions[item] > 0:
                if item not in recommendations:
                    recommendations[item] = similarity
                else:
                    recommendations[item] += similarity

    # Sort by score and return the top recommendations
    sorted_recommendations = sorted(recommendations.items(), key=lambda x: x[1], reverse=True)
    return [item for item, score in sorted_recommendations[:num_recommendations]]


@app.route('/recommend', methods=['GET'])
def recommend():
    user_id = int(request.args.get('user_id'))
    num_recommendations = int(request.args.get('num_recommendations', 3))
    dataTmp = None
    try:
        conn= psycopg2.connect(
            host = hostname,
            dbname = database,
            user = username,
            password = pwd,
            port = port_id
        )

        cur = conn.cursor()
        cur. execute('select DISTINCT cart_id, product_id from cart_line_item where is_deleted = true ORDER BY cart_id, product_id ')
        rows = cur.fetchall()
        data = {
        'userId': [row[0] for row in rows],
        'itemId': [row[1] for row in rows]
        }
        dataTmp = data
        cur.close()
        conn.close()
    except Exception as error:
        print(error)
    finally:
        if cur is not None:
            cur.close()
        if conn is not None:
            cur.close()
    
    interactions_df = pd.DataFrame(data)
    # Create a User-Item Matrix
    user_item_matrix = interactions_df.pivot_table(index='userId', columns='itemId', aggfunc='size', fill_value=0)

    if user_id not in user_item_matrix.index:
        return jsonify({'error': 'User not found'}), 404
    
    recommendations = get_user_recommendations(user_id, num_recommendations, dataTmp,interactions_df,user_item_matrix)
    return jsonify({'user_id': user_id, 'recommendations': recommendations})


if __name__ == '__main__':
    app.run(debug=True)
