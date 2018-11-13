import collections.defaultdict as defaultdict
import CGRtools.preparer.CGRpreparer as CGRpreparer
import logging.warning as warning
import numpy.array as array
import random.random as random
import random.shuffle as r_shuffle
import sklearn.model_selection.BaseCrossValidator as BaseCrossValidator
import sklearn.utils.validation.indexable as indexable


class TransformationOut(BaseCrossValidator):
    def __init__(self, n_splits=5, n_repeats=5, shuffle=False):
        self.n_splits = n_splits
        self.shuffle = shuffle
        self.n_repeats = n_repeats

    def get_n_splits(self, X=None, y=None, groups=None):
        return self.n_splits

    def split(self, X, y=None, groups=None):
        X, y, groups = indexable(X, y, groups)
        cgr = CGRpreparer()
        cgrs = [cgr.condense(r) for r in X]

        condition_structure = defaultdict(set)

        for structure, condition in zip(cgrs, groups):
            condition_structure[condition].add(structure)

        train_data = defaultdict(list)
        test_data = []

        for n, (structure, condition) in enumerate(zip(cgrs, groups)):
            train_data[structure].append(n)
            if len(condition_structure[condition]) > 1:
                test_data.append(n)

        if self.n_splits > len(train_data):
            raise ValueError("Cannot have number of splits n_splits=%d greater"
                             " than the number of transformations: %d."
                             % (self.n_splits, len(train_data)))

        structures_weight = sorted(((x, len(y)) for x, y in train_data.items()), key=lambda x: x[1], reverse=True)
        fold_mean_size = len(cgrs) // self.n_splits

        if structures_weight[0][1] > fold_mean_size:
            warning('You have transformation that greater fold size')

        for idx in range(self.n_repeats):
            folds = [[] for _ in range(self.n_splits)]
            for structure, structure_length in structures_weight:
                if self.shuffle:
                    r_shuffle(folds)
                for n, fold in enumerate(folds):
                    if len(fold) + structure_length <= fold_mean_size:
                        fold.extend(train_data[structure])
                        break
                    else:
                        roulette_param = (structure_length - fold_mean_size + len(fold)) / structure_length
                        if random() > roulette_param:
                            fold.extend(train_data[structure])
                            break
                        elif n == 4:
                            fold.extend(train_data[structure])

            for i in range(len(folds)):
                train_index = []
                test_index = []
                for j in range(self.n_splits):
                    if not j == i:
                        train_index.extend(folds[j])
                    else:
                        for c in folds[j]:
                            if groups is not None:
                                if c in test_data:
                                    test_index.append(c)
                            else:
                                test_index.append(c)
                yield array(train_index), array(test_index)
