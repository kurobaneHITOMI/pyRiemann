"""
====================================================================
Decoding in sensor space data using Riemannian Geometry and XDAWN
====================================================================

"""
# Authors: Alexandre Gramfort <alexandre.gramfort@telecom-paristech.fr>
#          Romain Trachel <romain.trachel@inria.fr>
#          Alexandre Barachant <alexandre.barachant@gmail.com>
#
# License: BSD (3-clause)

import numpy as np
from pylab import *
from pyriemann.estimation import XdawnCovariances
from pyriemann.classification import MDM,FgMDM

import mne
from mne import io
from mne.datasets import sample

from sklearn.pipeline import Pipeline  # noqa
from sklearn.cross_validation import KFold
from sklearn.metrics import classification_report,confusion_matrix
from sklearn.linear_model import LogisticRegression

print(__doc__)

data_path = sample.data_path()

###############################################################################
# Set parameters and read data
raw_fname = data_path + '/MEG/sample/sample_audvis_filt-0-40_raw.fif'
event_fname = data_path + '/MEG/sample/sample_audvis_filt-0-40_raw-eve.fif'
tmin, tmax = -0., 1
event_id = dict(aud_l=1,aud_r=2, vis_l=3,vis_r=4)

# Setup for reading the raw data
raw = io.Raw(raw_fname, preload=True)
raw.filter(2, None, method='iir')  # replace baselining with high-pass
events = mne.read_events(event_fname)

raw.info['bads'] = ['MEG 2443']  # set bad channels
picks = mne.pick_types(raw.info, meg='grad', eeg=False, stim=False, eog=False,
                       exclude='bads')

# Read epochs
epochs = mne.Epochs(raw, events, event_id, tmin, tmax, proj=False,
                    picks=picks, baseline=None, preload=True)

labels = epochs.events[:, -1]
evoked = epochs.average()

###############################################################################
# Decoding in sensor space using a linear SVM


n_components = 3  # pick some components

# Define a monte-carlo cross-validation generator (reduce variance):
cv = KFold(len(labels), 10,shuffle=True, random_state=42)
pr = np.zeros(len(labels))
epochs_data = epochs.get_data()



print('Multiclass classification with XDAWN + MDM')
clf = Pipeline([('COV',XdawnCovariances(n_components)),('MDM',MDM())])

for train_idx, test_idx in cv:
    y_train, y_test = labels[train_idx], labels[test_idx]
    
    clf.fit(epochs_data[train_idx], y_train)
    pr[test_idx] = clf.predict(epochs_data[test_idx])

print classification_report(labels,pr)
print confusion_matrix(labels,pr)

print('Multiclass classification with XDAWN + FgMDM')
clf = Pipeline([('COV',XdawnCovariances(n_components)),('MDM',FgMDM())])

for train_idx, test_idx in cv:
    y_train, y_test = labels[train_idx], labels[test_idx]
    
    clf.fit(epochs_data[train_idx], y_train)
    pr[test_idx] = clf.predict(epochs_data[test_idx])

print classification_report(labels,pr)
print confusion_matrix(labels,pr)

# spatial patterns
xd = XdawnCovariances(n_components)
Cov = xd.fit_transform(epochs_data,labels)

evoked.data = xd.Xd._patterns.T
evoked.times = np.arange(evoked.data.shape[0])
evoked.plot_topomap(times=[0, n_components, 2*n_components,3*n_components], ch_type='grad',
                    colorbar=False, size=1.5)
                    
# prototyped covariance matrices
mdm = MDM()
mdm.fit(Cov,labels)
fig,axe = plt.subplots(1,4)
axe[0].matshow(mdm.covmeans[0])
axe[0].set_title('Class 1 covariance matrix')
axe[1].matshow(mdm.covmeans[1])
axe[1].set_title('Class 2 covariance matrix')
axe[2].matshow(mdm.covmeans[2])
axe[2].set_title('Class 3 covariance matrix')
axe[3].matshow(mdm.covmeans[3])
axe[3].set_title('Class 4 covariance matrix')
plt.show()