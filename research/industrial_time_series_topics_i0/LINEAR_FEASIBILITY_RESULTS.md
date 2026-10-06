# Sealed linear feasibility result — negative for the initial premise

Sealcommit **e95ba3657e16bda8d3cc060fef714425cdb472ab** 已push且remote SHA核對，之後才執行。Program/asset/batch-ID hashes吻合，95batch/oneproductcode1、66train/9validation/20futuretest；fixedtarget dissolution_av。20Ridgefits、0neural，總runtime約3.11s。不是cross-factoryreplication、不是strongneuralmethodcomparison。

| Frozen variant | Test MSE | RMSE (% release points) | R² | Relative MSE gain vs materials |
|---|---:|---:|---:|---:|
| Training mean | 20.0702 | 4.4800 | −0.0614 | N/A |
| Material/recipe Ridge | 18.6001 | 4.3128 | 0.0163 | Reference |
| Material + 15min process prefix | 24.6258 | 4.9624 | −0.3024 | −32.40% |
| Material + 60min process prefix | 30.8222 | 5.5518 | −0.6301 | −65.71% |
| Material + Gaussian-sham (matched feature count) | 26.2988 | 5.1282 | −0.3909 | −41.39% |
| Material + whole-batch process (unavailable-future oracle) | 36.4614 | 6.0383 | −0.9283 | −96.03% |

所有Ridgevariants的validation選alpha100，沒有結果後改grid。Prefix15雖優於sham，但未優於materials，故不滿足預先訊號premise或3%materialityreference。Prefix60/sham/oracle均未提供正向證據。Wholebatchoracle是一種固定summary+linearlearner，不是information-theoreticBayesoracle；其差不能證明未來trajectory無資訊。

結論：**INITIAL_LINEAR_PREMISE_NOT_SUPPORTED**。資料/runtime可做，但這個單一產品、固定cutoff、Ridge summary下不能支持「多看製程即可提高早期quality」。保留全部負對照與結果；不能換target/產品/模型，重新定義此次pilot為成功。MaterialsR²僅約0.016，也不是可部署qualitysensor。

Limitations：Test20batches、validation9、sharedrawlots、單一sourcefamily；feature/learnercapacity與noise可能限制效能，沒有穩定性/顯著性聲稱。Certificate/startavailability是假設，未nativeas-of驗證。不能否定所有非線性/完整trajectory模型，也不能以此解鎖neuralrescuerun。對選題的作用是降級Q1/Q4初始增量訊號，globalindustrial-topicgoal仍ACTIVE，繼續尋找更可守住的問題。

Machine-readable結果：[results/linear_feasibility.json](results/linear_feasibility.json)，execution/hashrecord：[provenance/linear_probe_execution.json](provenance/linear_probe_execution.json)。
