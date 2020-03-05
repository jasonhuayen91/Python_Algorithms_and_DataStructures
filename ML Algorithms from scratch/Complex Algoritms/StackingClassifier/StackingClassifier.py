import numpy as np
import concurrent.futures
import multiprocess_fitting


class StackingClassifier():
    ''' implemetion of  stack classifier, that allows to train base models in parallel'''
    def __init__(self, base_models, meta_model, kfold):
        self.base_models = base_models
        self.base_trained_models = None
        self.meta_model = meta_model
        self.kfold = kfold
        self.X_blend_train = None

    def fit(self, X_train, y_train, max_workers=3):
        # kfolds for cross-validation
        folds = list(self.kfold.split(X_train, y_train))
        
        # train base model in paralel
        with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
        
            executor_results_holder = [executor.submit(multiprocess_fitting.fit_base_learner, model,
                                                       X_train, y_train, folds, idx) 
                                      for idx, model in enumerate(self.base_models)]
        
            results = [executor_result.result() for executor_result in 
                       concurrent.futures.as_completed(executor_results_holder)]
        
        # save only one model
        self.base_trained_models = [result[0] for result in results] 
        
        # to release memory
        self.base_models = None 
        
        # train set for meta model
        self.X_blend_train = np.concatenate([np.array(result[1]).reshape(-1,1) for result in results], axis=1)
        
        # train meta model
        self.meta_model.fit(self.X_blend_train, y_train)
        
        return self
    
    def predict(self, X_test):
        # feature test set for meta model - single model
        X_blend_test = np.concatenate([model.predict_proba(X_test)[:,1].reshape(-1,1) 
                                       for model in self.base_trained_models], axis=1)
        
        return self.meta_model.predict(X_blend_test)

        
    def predict_proba(self, X_test):
        # feature test set for meta model - single model
        X_blend_test = np.concatenate([model.predict_proba(X_test)[:,1].reshape(-1,1) 
                                       for model in self.base_trained_models], axis=1)
        
        return self.meta_model.predict_proba(X_blend_test)
   