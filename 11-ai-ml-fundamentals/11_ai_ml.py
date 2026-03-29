"""
============================================================
11 - AI/ML FUNDAMENTALS WITH PYTHON
============================================================
This is why millions of people learn Python. The scientific
Python ecosystem (NumPy, Pandas, scikit-learn, Matplotlib)
is unmatched for data science and machine learning.

We'll cover: data manipulation, classical ML, model evaluation,
and the patterns that underpin all ML work.

Install: pip install numpy pandas scikit-learn matplotlib seaborn
============================================================
"""

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.preprocessing import StandardScaler, LabelEncoder, OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LinearRegression, LogisticRegression, Ridge, Lasso
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report, mean_squared_error, r2_score
)
from sklearn.impute import SimpleImputer
from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
import warnings
warnings.filterwarnings("ignore")


# ─────────────────────────────────────────────────────────────
# NUMPY — the foundation of scientific Python
# ─────────────────────────────────────────────────────────────
# NumPy arrays are fast because they're:
# 1. Stored in contiguous memory (like C arrays)
# 2. Operations are vectorized (run in compiled C/Fortran, not Python loops)
# The rule: if you're looping over a NumPy array, you're doing it wrong.

def numpy_fundamentals():
    print("=== NumPy ===")

    # Creating arrays
    a = np.array([1, 2, 3, 4, 5])
    b = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])

    print(f"Shape: {b.shape}")       # (3, 3)
    print(f"Dtype: {b.dtype}")       # int64
    print(f"Ndim:  {b.ndim}")        # 2

    # Creating special arrays
    zeros = np.zeros((3, 4))
    ones  = np.ones((2, 3))
    eye   = np.eye(3)                # identity matrix
    rand  = np.random.rand(3, 3)     # uniform [0, 1)
    randn = np.random.randn(3, 3)    # standard normal
    range_arr = np.arange(0, 10, 2)  # [0, 2, 4, 6, 8]
    linspace  = np.linspace(0, 1, 5) # [0, .25, .5, .75, 1]

    # Vectorized operations — NO loops needed!
    x = np.array([1.0, 2.0, 3.0, 4.0])
    print(x * 2)            # [2. 4. 6. 8.]
    print(x ** 2)           # [1. 4. 9. 16.]
    print(np.sqrt(x))       # [1. 1.41 1.73 2.]
    print(np.exp(x))        # [e^1, e^2, e^3, e^4]
    print(x + np.array([10, 20, 30, 40]))  # element-wise

    # Boolean indexing — POWERFUL for filtering
    data = np.array([15, 8, 22, 3, 45, 11, 33])
    mask = data > 15
    print(data[mask])           # [22 45 33]
    print(data[data % 2 == 0])  # [8 22]

    # Fancy indexing
    print(data[[0, 2, 4]])      # [15 22 45]
    data[data < 10] = 0         # set all values < 10 to 0

    # Matrix operations
    A = np.array([[1, 2], [3, 4]])
    B = np.array([[5, 6], [7, 8]])

    print(A @ B)                # matrix multiplication
    print(np.dot(A, B))         # same thing
    print(A.T)                  # transpose
    print(np.linalg.det(A))     # determinant
    print(np.linalg.inv(A))     # inverse
    eigenvalues, eigenvectors = np.linalg.eig(A)

    # Aggregations
    data = np.random.randn(100)
    print(f"Mean: {data.mean():.4f}")
    print(f"Std:  {data.std():.4f}")
    print(f"Min:  {data.min():.4f}")
    print(f"Max:  {data.max():.4f}")

    # Along an axis
    matrix = np.random.rand(4, 3)
    print(matrix.sum(axis=0))   # column sums (along rows)
    print(matrix.sum(axis=1))   # row sums (along columns)
    print(matrix.mean(axis=0))  # column means

    # Reshaping
    flat = np.arange(12)
    shaped = flat.reshape(3, 4)     # (12,) → (3, 4)
    back   = shaped.flatten()       # (3,4) → (12,)
    added_dim = flat[:, np.newaxis] # (12,) → (12, 1) — add dimension

    # Broadcasting — NumPy's superpower
    # Operations between arrays of different shapes work when shapes are compatible
    a = np.array([[1, 2, 3], [4, 5, 6]])  # (2, 3)
    b = np.array([10, 20, 30])            # (3,) — broadcast to (2, 3)
    print(a + b)    # [[11, 22, 33], [14, 25, 36]]


# ─────────────────────────────────────────────────────────────
# PANDAS — data manipulation and analysis
# ─────────────────────────────────────────────────────────────

def pandas_fundamentals():
    print("\n=== Pandas ===")

    # Create DataFrames
    df = pd.DataFrame({
        "name":   ["Alice", "Bob", "Carol", "Dave", "Eve"],
        "age":    [30, 25, 35, 28, 42],
        "city":   ["NYC", "Boston", "NYC", "LA", "Boston"],
        "salary": [95000, 72000, 120000, 85000, 150000],
        "score":  [8.5, 7.2, 9.1, None, 8.8],  # None → NaN
    })

    # Basic info
    print(df.head())            # first 5 rows
    print(df.tail(2))           # last 2 rows
    print(df.info())            # dtypes and non-null counts
    print(df.describe())        # statistics for numeric columns
    print(df.shape)             # (5, 5)
    print(df.dtypes)            # column types
    print(df.columns.tolist())  # ['name', 'age', 'city', 'salary', 'score']

    # Selection
    print(df["name"])           # Series (one column)
    print(df[["name", "age"]]) # DataFrame (multiple columns)
    print(df.iloc[0])           # row by integer position
    print(df.iloc[0:3, 1:3])   # rows 0-2, columns 1-2
    print(df.loc[0])            # row by label
    print(df.loc[df["age"] > 30, ["name", "salary"]])  # filter + select

    # Filtering — same as boolean indexing in NumPy
    nyc_people = df[df["city"] == "NYC"]
    high_earners = df[df["salary"] >= 100_000]
    senior_nyc = df[(df["city"] == "NYC") & (df["age"] >= 30)]  # AND
    boston_or_la = df[df["city"].isin(["Boston", "LA"])]          # isin

    # Missing data
    print(df.isnull().sum())         # count nulls per column
    print(df.isnull().any())         # which columns have nulls?
    df_filled  = df.fillna(df["score"].mean())      # fill with mean
    df_dropped = df.dropna()                         # drop rows with any null
    df_ffill   = df.fillna(method="ffill")           # forward fill

    # Adding/modifying columns
    df["senior"] = df["age"] > 35
    df["salary_k"] = df["salary"] / 1000
    df["name_upper"] = df["name"].str.upper()        # vectorized string ops!
    df["city_clean"] = df["city"].str.strip().str.lower()

    # apply — apply a function to each row/column
    df["score_category"] = df["score"].apply(
        lambda x: "high" if x >= 9 else ("medium" if x >= 7 else "low")
    )
    # For row-wise operations:
    df["summary"] = df.apply(
        lambda row: f"{row['name']} from {row['city']} earns ${row['salary']:,}",
        axis=1  # axis=1 means apply function to each row
    )

    # GroupBy — the SQL GROUP BY equivalent
    city_stats = df.groupby("city").agg(
        count=("name", "count"),
        avg_salary=("salary", "mean"),
        max_age=("age", "max"),
        total_salary=("salary", "sum"),
    ).reset_index()
    print(city_stats)

    # Sort and rank
    df_sorted = df.sort_values(["city", "salary"], ascending=[True, False])
    df["salary_rank"] = df["salary"].rank(ascending=False).astype(int)

    # Merge/Join — like SQL JOINs
    skills = pd.DataFrame({
        "name": ["Alice", "Bob", "Carol", "Frank"],
        "skill": ["Python", "Java", "Python", "Go"]
    })
    merged = df.merge(skills, on="name", how="left")  # LEFT JOIN
    inner  = df.merge(skills, on="name", how="inner")  # INNER JOIN

    # Pivot tables — reshaping data
    pivot = df.pivot_table(
        values="salary",
        index="city",
        aggfunc=["mean", "count", "sum"]
    )
    print(pivot)

    # Reading/writing data
    # df.to_csv("output.csv", index=False)
    # df = pd.read_csv("data.csv")
    # df.to_json("output.json", orient="records")
    # df = pd.read_excel("data.xlsx", sheet_name="Sheet1")

    return df


# ─────────────────────────────────────────────────────────────
# THE ML WORKFLOW — same pattern every time
# ─────────────────────────────────────────────────────────────

def ml_workflow_example():
    """
    The standard ML workflow:
    1. Load and explore data
    2. Clean and preprocess
    3. Feature engineering
    4. Split train/test
    5. Build preprocessing pipeline
    6. Train model
    7. Evaluate
    8. Tune hyperparameters
    9. Evaluate on test set
    10. Deploy
    """
    print("\n=== ML Workflow: Iris Classification ===")

    from sklearn.datasets import load_iris, load_boston_fields
    from sklearn.datasets import load_iris

    # 1. Load data
    iris = load_iris()
    X = iris.data           # (150, 4) — 150 samples, 4 features
    y = iris.target         # (150,)   — 0, 1, or 2
    feature_names = iris.feature_names
    target_names  = iris.target_names

    print(f"Features: {feature_names}")
    print(f"Classes: {target_names}")
    print(f"Shape: X={X.shape}, y={y.shape}")

    # 2. Split train/test FIRST — never touch test data during development!
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=0.2,      # 20% for testing
        random_state=42,    # reproducibility
        stratify=y          # maintain class distribution in both splits
    )

    # 3. Build a Pipeline — preprocessing + model in one object
    # This is crucial: fit only on training data, apply to both train AND test
    pipeline = Pipeline([
        ("scaler", StandardScaler()),              # normalize features
        ("classifier", RandomForestClassifier(    # the model
            n_estimators=100,
            random_state=42
        )),
    ])

    # 4. Cross-validation — more reliable than a single train/test split
    cv_scores = cross_val_score(pipeline, X_train, y_train, cv=5, scoring="accuracy")
    print(f"\nCV Accuracy: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")

    # 5. Train on all training data
    pipeline.fit(X_train, y_train)

    # 6. Evaluate on test set
    y_pred = pipeline.predict(X_test)
    y_prob = pipeline.predict_proba(X_test)  # class probabilities

    print(f"\nTest Accuracy:  {accuracy_score(y_test, y_pred):.4f}")
    print(f"Precision:      {precision_score(y_test, y_pred, average='weighted'):.4f}")
    print(f"Recall:         {recall_score(y_test, y_pred, average='weighted'):.4f}")
    print(f"F1 Score:       {f1_score(y_test, y_pred, average='weighted'):.4f}")

    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=target_names))

    print("Confusion Matrix:")
    print(confusion_matrix(y_test, y_pred))

    # 7. Feature importance (tree-based models)
    rf = pipeline.named_steps["classifier"]
    importances = pd.Series(rf.feature_importances_, index=feature_names)
    print("\nFeature Importances:")
    print(importances.sort_values(ascending=False))


# ─────────────────────────────────────────────────────────────
# PREPROCESSING PIPELINE — the RIGHT way to handle mixed data
# ─────────────────────────────────────────────────────────────

def preprocessing_pipeline_example():
    """Handle numeric, categorical, and text features correctly."""
    print("\n=== Preprocessing Pipeline ===")

    # Sample dataset with mixed types
    data = pd.DataFrame({
        "age":    [25, 32, None, 45, 28],
        "salary": [50000, 85000, 72000, None, 63000],
        "city":   ["NYC", "LA", "NYC", "Boston", "LA"],
        "edu":    ["Bachelor", "Master", "PhD", "Bachelor", "Master"],
        "score":  [7.5, 8.2, 9.0, 6.8, 7.9],
    })
    target = [0, 1, 1, 0, 1]

    # Separate columns by type
    numeric_features     = ["age", "salary", "score"]
    categorical_features = ["city", "edu"]

    # Build separate pipelines for each type
    numeric_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),  # fill NaN with median
        ("scaler",  StandardScaler()),                   # normalize
    ])

    categorical_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),  # fill NaN with mode
        ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
    ])

    # Combine with ColumnTransformer
    preprocessor = ColumnTransformer([
        ("num", numeric_pipeline,     numeric_features),
        ("cat", categorical_pipeline, categorical_features),
    ])

    # Full pipeline
    full_pipeline = Pipeline([
        ("preprocessor", preprocessor),
        ("classifier",   LogisticRegression(max_iter=1000)),
    ])

    X = data
    y = np.array(target)

    full_pipeline.fit(X, y)
    predictions = full_pipeline.predict(X)
    print(f"Training accuracy: {accuracy_score(y, predictions):.4f}")


# ─────────────────────────────────────────────────────────────
# HYPERPARAMETER TUNING
# ─────────────────────────────────────────────────────────────

def hyperparameter_tuning():
    print("\n=== Hyperparameter Tuning ===")
    from sklearn.datasets import load_iris

    X, y = load_iris(return_X_y=True)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Grid Search — exhaustive search over parameter grid
    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("clf",    RandomForestClassifier(random_state=42)),
    ])

    param_grid = {
        "clf__n_estimators": [50, 100, 200],
        "clf__max_depth": [None, 5, 10],
        "clf__min_samples_split": [2, 5],
    }
    # Note: prefix with pipeline step name + __

    grid_search = GridSearchCV(
        pipeline, param_grid,
        cv=5,                   # 5-fold cross-validation
        scoring="accuracy",
        n_jobs=-1,              # use all CPU cores
        verbose=1,
    )
    grid_search.fit(X_train, y_train)

    print(f"Best params:    {grid_search.best_params_}")
    print(f"Best CV score:  {grid_search.best_score_:.4f}")
    print(f"Test accuracy:  {accuracy_score(y_test, grid_search.predict(X_test)):.4f}")

    # RandomizedSearchCV — faster, good enough for large spaces
    from sklearn.model_selection import RandomizedSearchCV
    from scipy.stats import randint, uniform

    param_dist = {
        "clf__n_estimators": randint(50, 300),
        "clf__max_depth": randint(3, 20),
        "clf__min_samples_split": randint(2, 10),
        "clf__max_features": uniform(0.3, 0.7),
    }

    random_search = RandomizedSearchCV(
        pipeline, param_dist,
        n_iter=20,      # try 20 random combinations
        cv=5,
        scoring="accuracy",
        n_jobs=-1,
        random_state=42,
    )
    # random_search.fit(X_train, y_train)


# ─────────────────────────────────────────────────────────────
# MODEL COMPARISON — pick the best algorithm
# ─────────────────────────────────────────────────────────────

def compare_models():
    print("\n=== Model Comparison ===")
    from sklearn.datasets import load_iris

    X, y = load_iris(return_X_y=True)

    models = {
        "Logistic Regression": LogisticRegression(max_iter=1000),
        "Decision Tree":        DecisionTreeClassifier(max_depth=5),
        "Random Forest":        RandomForestClassifier(n_estimators=100, random_state=42),
        "Gradient Boosting":    GradientBoostingClassifier(random_state=42),
        "SVM":                  SVC(probability=True),
        "KNN":                  KNeighborsClassifier(n_neighbors=5),
    }

    results = {}
    for name, model in models.items():
        pipeline = Pipeline([
            ("scaler", StandardScaler()),
            ("model",  model),
        ])
        scores = cross_val_score(pipeline, X, y, cv=5, scoring="accuracy")
        results[name] = {"mean": scores.mean(), "std": scores.std()}
        print(f"{name:25s}: {scores.mean():.4f} ± {scores.std():.4f}")

    best = max(results, key=lambda k: results[k]["mean"])
    print(f"\nBest model: {best} ({results[best]['mean']:.4f})")


# ─────────────────────────────────────────────────────────────
# SAVING AND LOADING MODELS
# ─────────────────────────────────────────────────────────────

def model_persistence():
    import joblib  # pip install joblib — much better than pickle for sklearn
    from sklearn.datasets import load_iris
    from pathlib import Path

    X, y = load_iris(return_X_y=True)
    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", RandomForestClassifier(n_estimators=100, random_state=42))
    ])
    pipeline.fit(X, y)

    # Save
    model_path = Path("models/iris_classifier.joblib")
    model_path.parent.mkdir(exist_ok=True)
    joblib.dump(pipeline, model_path)
    print(f"Model saved to {model_path}")

    # Load
    loaded = joblib.load(model_path)
    predictions = loaded.predict(X[:5])
    print(f"Loaded model predictions: {predictions}")

    # Also works with MLflow for tracking (enterprise)
    # import mlflow
    # mlflow.sklearn.log_model(pipeline, "model")


if __name__ == "__main__":
    numpy_fundamentals()
    pandas_fundamentals()
    ml_workflow_example()
    preprocessing_pipeline_example()
    hyperparameter_tuning()
    compare_models()
