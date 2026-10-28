"""
CareerPulse — Feature engineering module.

Builds feature matrices from cleaned data for ML model training.
Combines TF-IDF text features with structured/numerical features.
"""

import logging
from pathlib import Path
from typing import Tuple

import numpy as np
import pandas as pd
import scipy.sparse as sp

logger = logging.getLogger(__name__)


def combine_features(tfidf_matrix, structured_df: pd.DataFrame):
    """
    Horizontally concatenate TF-IDF sparse matrix with structured numerical features.

    Parameters
    ----------
    tfidf_matrix : sparse matrix (n_samples, n_tfidf_features)
    structured_df : DataFrame of numerical features (n_samples, n_struct_features)

    Returns
    -------
    Combined sparse matrix (n_samples, n_tfidf + n_struct)
    """
    structured_sparse = sp.csr_matrix(structured_df.values.astype(np.float64))
    combined = sp.hstack([tfidf_matrix, structured_sparse], format="csr")
    logger.debug(
        "Combined feature matrix: %d samples, %d features (%d TF-IDF + %d structured)",
        combined.shape[0], combined.shape[1],
        tfidf_matrix.shape[1], structured_df.shape[1],
    )
    return combined


def build_feature_report(
    X_train, X_val, X_test, y_train, y_val, y_test, class_names: list
) -> dict:
    """Return a concise report of feature/split dimensions for logging."""
    return {
        "train_samples": X_train.shape[0],
        "val_samples": X_val.shape[0],
        "test_samples": X_test.shape[0],
        "n_features": X_train.shape[1],
        "train_class_dist": dict(zip(class_names, np.bincount(y_train, minlength=len(class_names)).tolist())),
        "val_class_dist": dict(zip(class_names, np.bincount(y_val, minlength=len(class_names)).tolist())),
        "test_class_dist": dict(zip(class_names, np.bincount(y_test, minlength=len(class_names)).tolist())),
    }
