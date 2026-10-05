# Whole-trace normal split

| trace | role | sha256 |
| --- | --- | --- |
| 6_0_100000_46 | fit | 07c1b845b50f51ca9c9200c7ad154a8440f3919d7ec216960e0e220392d52568 |
| 6_0_50000_48 | validation | c5c251a3b2c6ad12451c895aeb61442f151abba1cdf9892e3d1785449c389a43 |
| 6_0_50000_49 | calibration | d48dd1352e1d07a63493777bc0fa757ef0043e0ed5fd8745f91ceaf1719d1d22 |
| 6_0_50000_51 | normal_control | b811e8ab7649991c35564e52b1d7b70886248d4cd082c606712575768442861b |
| 9_0_100000_1 | fit | ec07c0a04a489384236859b4195bd5ee9d2f354a5bc93036e9bddded9fa3c865 |
| 9_0_100000_3 | validation | fb223ecb8fc63ef3d130ca9dfe7da7c4816766a1e9a994f102f1c23671ed1a65 |
| 9_0_300000_5 | calibration | 1f57d393c8bffa9e2fef426d934d010d978efddc10783f0711c8977989222add |
| 9_0_100000_6 | normal_control | 4325bb7691438b06a409d2dedfd997f3d96f613ec72b5fb3304527a8bdbb3ab1 |
| 10_0_100000_8 | fit | 318a565481623e73198942ae22c1812432b136a26f4c1f858d07df0ccba74c36 |
| 10_0_100000_9 | validation | 3ccbfc345bb7b67a1c2e5147d63c5e8e508aa41de1c8ec21a53c8a045d0d0175 |
| 10_0_100000_10 | calibration | 15379b1da6c9ead6d92ed964d0f062c061a663d19dcc67c751756e41137bfdaa |
| 10_0_100000_11 | normal_control | e4c750d75b4d480ee4a7f6666a6bb8dcdb27ebb8159d06dfd72aa291104ba87b |
| 10_3_1000000_75 | disturbed | 6f617b7475162157c93d448e88806861f77fd7e3554e00136d0d168d006946c6 |
| 10_4_1000000_79 | disturbed | 0f99cc76e0771a89b32d1d79ef1f6e5f87e6aae66622e62e5e4c4221d2db02d6 |
| 6_1_500000_65 | disturbed | e8a77aa39bd79cfd923155a967f1294ecb7d4c53f180de1e983aac30c537c847 |
| 6_3_200000_76 | disturbed | e9eca9560c35e5dfbf91431f3f2334bfd9de1e71987bdad00f2d22f6ab7b06e0 |
| 9_3_500000_74 | disturbed | beeb1f20d52f6cd149bdcbf2332f0f1e5df94d416261fb08d61da5f9470e77b5 |
| 9_4_1000000_78 | disturbed | ad74b59277fe98da8b663578eb6bfda8de9455eb0660970b10c0c834c5bf863f |
| 10_2_1000000_67 | crash_control | e12026ea04ba2e7b6f42a51bc436e7acd3521756f03ee34a30b92ccf759df55e |

Four smallest single-ZIP normal archives per app are selected by released byte size and numeric ID tie; their ascending numeric IDs assign fit/validation/calibration/normal_control. Multipart traces are excluded before outcomes to bound acquisition. This yields one trace per app per role. App6’s selected normal contexts have low rates; app9/app10 differ. It is a bounded global reference, not matched-context training.

No random-window overlap between roles. scaler/PCA/LSTM only use fit traces, every one officially undisturbed. Validation diagnostics cannot choose epoch/model. Whole independent calibration traces set normalq.995 and IQR; normal_control traces only supply FPR and duration controls. Disturbed labels are read only by the evaluator after training. Exact timestamps/features/arrays are independently hashed in the manifests.

Offline frozen-model causal input availability is tested; this is not a claim of chronologically deployed2018 model fitting. Shared cluster executions and app/type resource confounds remain dependencies.
