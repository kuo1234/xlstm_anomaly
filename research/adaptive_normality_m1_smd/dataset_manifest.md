# M1-A SMD dataset manifest

> Descriptive data/provenance audit only. No detector, training, model selection, or score evaluation was run. The preprocessing rule and W=256 were frozen from the original training splits before test-label values were parsed. Test labels below are used only for schema/prevalence/event inventory.

## Source and verification

- Upstream: [NetManAIOps/OmniAnomaly](https://github.com/NetManAIOps/OmniAnomaly), commit `7fb0e0acf89ea49908896bcc9f9e80fcfff6baf4`.
- Pinned raw layout: `ServerMachineDataset/{train,test,test_label}/{machine}.txt`. All 84 source files (28 machines × 3 splits) were fetched from commit-addressed HTTPS raw URLs; 84/84 completed, no fetch errors. SHA-256 and byte size are listed below.
- Every file parses as finite numeric comma-separated rows. Each observation has 38 columns; each label vector is binary and has the same length as that machine’s test trace. No machine failed provenance/schema checks; all 28 remain in the prospective cohort.
- The 28 pre-existing local test traces at `data/phase_a/smd_raw/*_test.txt` were compared against the pinned download; all 28 byte-match.
- SMD has 3 machine groups (1, 2, 3). The original README says 28 machines, 38 dimensions, and per-machine train/test partitions; `test_label` gives point anomaly labels and `interpretation_label` is a separate contributing-dimension annotation. The original files have no headers or stable KPI names; channel positions are retained exactly and no channel reordering is allowed. Within-machine train/test positional correspondence follows the official file schema. Cross-machine semantic equivalence of the 38 positions is not documented, so M1 fits and scores each machine independently and never pools channel meanings.

## Machine inventory

| Machine | D | Train rows | Test rows | Positive test points | Test prevalence | Contiguous label runs |
|---|---:|---:|---:|---:|---:|---:|
| machine-1-1 | 38 | 28479 | 28479 | 2694 | 9.4596% | 8 |
| machine-1-2 | 38 | 23694 | 23694 | 542 | 2.2875% | 10 |
| machine-1-3 | 38 | 23702 | 23703 | 817 | 3.4468% | 12 |
| machine-1-4 | 38 | 23706 | 23707 | 720 | 3.0371% | 12 |
| machine-1-5 | 38 | 23705 | 23706 | 100 | 0.4218% | 7 |
| machine-1-6 | 38 | 23688 | 23689 | 3708 | 15.6528% | 30 |
| machine-1-7 | 38 | 23697 | 23697 | 2398 | 10.1194% | 13 |
| machine-1-8 | 38 | 23698 | 23699 | 763 | 3.2195% | 20 |
| machine-2-1 | 38 | 23693 | 23694 | 1170 | 4.9380% | 13 |
| machine-2-2 | 38 | 23699 | 23700 | 2833 | 11.9536% | 11 |
| machine-2-3 | 38 | 23688 | 23689 | 269 | 1.1355% | 10 |
| machine-2-4 | 38 | 23689 | 23689 | 1694 | 7.1510% | 20 |
| machine-2-5 | 38 | 23688 | 23689 | 980 | 4.1369% | 21 |
| machine-2-6 | 38 | 28743 | 28743 | 424 | 1.4751% | 8 |
| machine-2-7 | 38 | 23696 | 23696 | 417 | 1.7598% | 20 |
| machine-2-8 | 38 | 23702 | 23703 | 161 | 0.6792% | 1 |
| machine-2-9 | 38 | 28722 | 28722 | 1755 | 6.1103% | 10 |
| machine-3-1 | 38 | 28700 | 28700 | 308 | 1.0732% | 4 |
| machine-3-2 | 38 | 23702 | 23703 | 1109 | 4.6787% | 10 |
| machine-3-3 | 38 | 23703 | 23703 | 632 | 2.6663% | 26 |
| machine-3-4 | 38 | 23687 | 23687 | 977 | 4.1246% | 8 |
| machine-3-5 | 38 | 23690 | 23691 | 426 | 1.7982% | 11 |
| machine-3-6 | 38 | 28726 | 28726 | 1194 | 4.1565% | 11 |
| machine-3-7 | 38 | 28705 | 28705 | 434 | 1.5119% | 5 |
| machine-3-8 | 38 | 28703 | 28704 | 1371 | 4.7763% | 6 |
| machine-3-9 | 38 | 28713 | 28713 | 303 | 1.0553% | 4 |
| machine-3-10 | 38 | 23692 | 23693 | 1047 | 4.4190% | 13 |
| machine-3-11 | 38 | 28695 | 28696 | 198 | 0.6900% | 3 |

- Totals: **28 machines**, **708,405 train rows**, **708,420 test rows**, **D=38 for every file**, **29,444 positive test points** (4.1563% micro prevalence), and **327 contiguous binary-label runs**. Across machines, train rows range 23,687–28,743; test rows range 23,687–28,743. Train/test lengths differ by at most one row within each machine.
- Test-only machine prevalence spans 0.4218%–15.6528%; the family is heterogeneous. The contiguous-run lengths range 2–3,161 points (median 11). Runs are a reproducible proxy from binary labels, not incident identifiers; contiguous labels can merge separate incidents or split one incident.

## File seals

Every digest below is SHA-256 of the raw bytes downloaded from the pinned upstream commit. Filenames are the exact official machine IDs.

| Machine | Train bytes / SHA-256 | Test bytes / SHA-256 | Test-label bytes / SHA-256 |
|---|---|---|---|
| machine-1-1 | 9,739,818 / `ecebd2933ccdc1126e2abbfb538762dbde16410cebc77257a7b96e1e1fbcf753` | 9,739,818 / `bdb801d8d52ce6b0c4a20c310edf31b5cee9bc82eb84fb38e7d4a19309b16ddb` | 56,958 / `cddf33441ae480c6074e173c897d4715eb893f24a7078d3d3e1b79b200c7cd19` |
| machine-1-2 | 8,103,348 / `7f6f63ec34ce616c87b4c30d66fd52ad1b21149634ae3ff7bb1827a76d6ef79a` | 8,103,348 / `f409991af7c049d3f286a8cf89dc2fa99114bea8753f6c3aea4bd24cb03eb015` | 47,388 / `c2dbb3e4f89c9eb48f30fd1ddae48b80e7ae7ad7ca9abf2ffd71b6557ef2bb20` |
| machine-1-3 | 8,106,084 / `a4ef16a49d921e0ba9497ce2690d3833eb4a85f9a8a88392de4c3fde42e413ac` | 8,106,426 / `f3c134d45ffa7aed66587dba893111396c8c7ea3b6fa7f76895955b26b1a75ef` | 47,406 / `755d57179625682172ae85f9483749cff576ff3282d0af294271a40ab6ea7b28` |
| machine-1-4 | 8,107,452 / `2ec56c43f91684aa4751a6b72d359669266712dd69bdc7efda3dc60c0ade1156` | 8,107,794 / `98ade00e57eac63e8f81a506a8e848803b58590835ab2b3cf53d1f0459900bd3` | 47,414 / `a470a3f7b66ec3d080fc5ee3d9565e0f3bfcfa16a1650259f771736327fa9a8b` |
| machine-1-5 | 8,107,110 / `69061055f43413863434cb9c0424c14b13a7a0817056a8fd9439e53dc365fc0b` | 8,107,452 / `98b8979f21b4b68c7308f38dd093b9bff4275814578365103c692f28f60f61c5` | 47,412 / `e7e2e611e12b5e9e2558ed955ad271f1f408fbdd7fbbfdfc72eb745ade567815` |
| machine-1-6 | 8,101,296 / `27e1765c04c2a5d08f39d98e7979e7764886fc733c36382fe081157a5ac0b9d8` | 8,101,638 / `0797fe4bfd25ef13c830955cb9f2a36b4c9d5da265b8e91702408b6b048267f4` | 47,378 / `8359ffa67b5421b0b9967ccf396a58c7b3bf52fa24c3f95e6b9df6486f1d6365` |
| machine-1-7 | 8,104,374 / `dddb9f770bdb8b1b952263e0cc4f000b6f8ec612941dd3eb7a303994f257edf8` | 8,104,374 / `785a3f542ef6ac171a3af55c534f9ca598d53fa0371010172c72e33af4588d16` | 47,394 / `24b3ce00bf2c56b571775a2b28d4e50ed27d050d77a031fa16c11ef3e51809b8` |
| machine-1-8 | 8,104,716 / `3b46e9754ec06bebd0bf3fe68dbe28b2a4b67298e795c9501d97f42083e337fc` | 8,105,058 / `b8784c3b4169f8a0a2ed9f47b00070d72ed214dae0307553b8cfdb80c712d779` | 47,398 / `8019476032c4c5b4b80127cfb9e74ee7d57fbbd558aa15097518713e16463a47` |
| machine-2-1 | 8,103,006 / `d6eb13ff74a537cf33686319fffdd4cdcb394862570a3acd519b4c37af97cd2e` | 8,103,348 / `2d103661799271be958227907950a1c76803356442d60a4070671cc0abbefb20` | 47,388 / `416dd20a447f38b8d9394382293ed44f509c1c3f99c4aa2fbff179498626dbdc` |
| machine-2-2 | 8,105,058 / `e2e0f52994c8c884f9552c6289e42268d9d988ba7c7abadcc0d8dcd8ba993c30` | 8,105,400 / `1cb0dd0a4b8738b184c62bb07700e6800e029f7a76a715fe0ee147c603b2f2c8` | 47,400 / `b09e71b3aafe71d9ee73a4058b30efcf67dc80df98d3b7b7a8ec019ea3b769c4` |
| machine-2-3 | 8,101,296 / `d2b0fc37d08cb727438598a1b09ced94f71f7792a9b4d057242e2ce8f2580e13` | 8,101,638 / `eaa24c78ff438eec2f847c09eb4de6ab8dbe8a0bb8d77b52ac4ecdee5bd21a7d` | 47,378 / `5768ce5280cb5ce4bee6d8bb3c7105819574d5e82f7d517d61495efa9d4f566e` |
| machine-2-4 | 8,101,638 / `077a5c18649b9d260d8dcbd4cfbf10b16cb83719a52013410cf3b5dc6a802fa6` | 8,101,638 / `85ba3101b9ab6a7684cd897b2d4c78e85caa6f5ef1c4f0e153479f4fca01cf38` | 47,378 / `c26a6dabfd2ab4aec34c40919100e13e52e17ad0e6b702dd038f582b2c633b01` |
| machine-2-5 | 8,101,296 / `940cdf20a8345fdeeb8043efd7ce9f7506fe0e7f5f89f8b50edf19b61b304136` | 8,101,638 / `842588acfb9299735a785757fcadd98cc7f69b6a511d28e54e1af05c5e95137b` | 47,378 / `9966e4092bece4e0ef60ef54d85396c49c22da64334aad82a9fc2f3842d2ef15` |
| machine-2-6 | 9,830,106 / `dc30adaef939060aebea3836c691e3d1bb47da593fa43553acbc52c6825dc8ae` | 9,830,106 / `c895144b7c7fb1ff960f506132d5aeefebce4325efad908d071fb7df5b3b1cf1` | 57,486 / `6fe3dd209542dc6a20879618c40ef6f5d55ce60f2da2902c311d9f0fff3c1ee0` |
| machine-2-7 | 8,104,032 / `32e9d88b18bf1b377a2bd0a6d5de2a766f36c58781e76dbe2491b0347557dec2` | 8,104,032 / `58c3dfd109437ccbedab9d36608d32874c2ae5473484c5941f85349baf32cef8` | 47,392 / `d9d7aceca750277dd28883f7b5b34da3653652ea9c96de78baa84daeebc4a9b7` |
| machine-2-8 | 8,106,084 / `01ae9289566e3518cf738518a25edb0812f889e8ed1dada057f4693ac5dda23c` | 8,106,426 / `846207955c546f0c3ea57aa7032b8e3c207ad67632a0605c8273f182059d1a72` | 47,406 / `22fbe94e06e56b6035fcc10383bac90d84ff4604f9063009a3940747f92d8105` |
| machine-2-9 | 9,822,924 / `465db893338b6f14985dd30ac2ff20a319246bb8584cd0a9a4aaacf52cbc2f1f` | 9,822,924 / `8d93ccd1a6606de3f665cb2e905d206b60ad2b2a58f47e9561b9bb67a2cd4f28` | 57,444 / `eab9425847aa5c7c63485047a49b1bfc9cf44ed88a0d1be84e2fd0a16d0ba895` |
| machine-3-1 | 9,815,400 / `c1186ac085809c0590467dd42f4f12180012ebd994c1e615250dbed2a3588111` | 9,815,400 / `b110b204ba4919250351eba7aa253d73ab54af0cf18e272b9b284de5fa7df88d` | 57,400 / `549348a9c63ed922e85157885bcb21289a8c9f5af94b50147a21cb7b928220ec` |
| machine-3-2 | 8,106,084 / `7cabed178422f7772425c6cabc3c20a1f7dedc3ab2a950f90a9edfcef3b5b3e3` | 8,106,426 / `5f83ded5fbfb9b682030bdd7dd82eb53a77f9caa3773ddcc7e38db73c25db46e` | 47,406 / `1bbf4223cc6083f718f1d6022e2a48d48af44b08cdfa80048aa51af34d5111c3` |
| machine-3-3 | 8,106,426 / `6bbad775c6ef6319abba08aaa6faa2befb2cd570f9db85b80413ae6fdf1047a4` | 8,106,426 / `ecc3140ce24869a44ebac9b03ca372fb1a6eb7e5bde96946f1a350283d4b152a` | 47,406 / `4e2c657f613759f11f167c5540d047723d41d8a3c76467fa4daafcc8a7112035` |
| machine-3-4 | 8,100,954 / `a27a88c5d96c3384e07776dd2ced9956f7ea78b1070b87786352bc6024129d72` | 8,100,954 / `07e1b43e20b7d8300fcd4b4f45ea47ea8c851f3dbd7d1fe971139c32f039357e` | 47,374 / `5c1f09b85c53d1936eff1e044c5f7413b07f10fd641934b4aba9b2669485b7be` |
| machine-3-5 | 8,101,980 / `7eb4f157d5aace0f5758c8035a4cc90445fc0d3ae59c57b1bf00d7e62c363bba` | 8,102,322 / `85dbb13b3076981ad917f42081b71a1440d8b2aafd9bee626f0d1cacff43fcd6` | 47,382 / `8a17a0dff8cc0062124997d665a2055cc1c08daffffb9a63ccfd21f7d10bea8f` |
| machine-3-6 | 9,824,292 / `88b8164dccfe67704e83c0919aa40bf1d4b8d682aff0b947d4cdd1ec4f900b84` | 9,824,292 / `04f746a4dde41adbfe5727c6ff77839d1b0b21d6d65bdb0253557e0391c5d44c` | 57,452 / `2bef9db1d998172c61008f593a7537377179ef4f24963001203c1e48345e9b61` |
| machine-3-7 | 9,817,110 / `5eb1f16e62c30eb498e968b2c6da3e8f60c8367e264f771245a970362d7d8574` | 9,817,110 / `a4588c1f39905d03bd24fce65052e7b175fba336d081843325ef780c9ed8cdad` | 57,410 / `80b3a19dfd0af2d800c2388474543bdcb723ba582b0f4a986d68f920b757c73c` |
| machine-3-8 | 9,816,426 / `414ba622ae70118948a3940009ce4e90580b494ea07f9e03893c26e102edd855` | 9,816,768 / `fa79d5dad3a703fbc13faf0eab26d9466b74789f2bb0d22776f2adaa4236f085` | 57,408 / `dc834a5b5e9a194f5367423c29410afcb622e0e47d7d3362979dd280de713220` |
| machine-3-9 | 9,819,846 / `7896b57b65da1d48ee992ba128fb914ae7e6d2bef8ea4ed8df039657fc017468` | 9,819,846 / `5a8968c269a8a3562e54235aa05344b262f44829c2bae04cf9f5d364f388310d` | 57,426 / `bdaf308affb4653e3e5826177e7e27c883294d2fa8cf48364850ef5a4dac2282` |
| machine-3-10 | 8,102,664 / `8f8258b3a85fe8aa5badb05e66b0cdd3405be5f180f0d418bc24c30503207fd2` | 8,103,006 / `febaf197d4a8864f3a70a5e5c0926d6dab8f1b515cf0d90d31ee81a22d80392f` | 47,386 / `d2b87c9c1d1950f0b29eaca0edf4706b917984799f6d9b5c1472435832fe3abd` |
| machine-3-11 | 9,813,690 / `a2e531cf2bf9b8d833a0b6e7c42a596b1d3a64578a1c140537add46156bde4e9` | 9,814,032 / `c62f52e65d1b892ef8c556b38aa5c1d3504cf0cdd97a94e7df08985b922d7af0` | 57,392 / `ce306777bd66e9ea81de726018e440d49afcc98415cb0db7d99367dddf398f1b` |

## Train normality and limits

- The benchmark convention treats each machine’s first split as normal training data. The original upstream README describes the first half as train and the latter half as test, with expert incident-based anomaly labels on test; it does not provide a separate train-label file. A 2026 SMD re-audit explicitly describes the training behavior as normal and the test as labeled anomalies. Thus train normality is a benchmark assumption supported by published protocol, not pointwise ground-truth verification. Any contamination of the train split remains unmeasured.
- The raw traces contain no timestamps. Published SMD descriptions report equally spaced one-minute observations and about five weeks per machine; M1 reports all primary delays in samples and treats conversion to minutes as nominal only.
- Labels are pointwise 0/1. No point adjustment, event expansion, or test-label-based configuration is permitted. Anomaly prevalence and contiguous runs above are dataset audit fields only.
- R0 used only machine-1-8, machine-2-1, and machine-1-4. M1 retains all 28 regardless of those prior outcomes; no machine was selected from R0 performance.

## Repository utility compatibility

- The pinned source files use the same comma-separated 38-column layout expected by `scripts/real_data_r0_data.py`, and R0’s byte hashing and finite/shape validation patterns are reusable.
- The R0 utility is allow-listed to three machines and its manifest/scaler are frozen to R0. M1 therefore requires a separate 28-machine manifest/loader; do not widen or edit the R0 utility/config in place. R0’s zero-std-only transform is expressly not used.
- Test labels are evaluator-only in M1 execution. The loader must expose them only after predictions are sealed, for metric calculation; they are never an input to preprocessing, context choice, training, checkpoint selection, or threshold calibration.

## Source references

- [Official OmniAnomaly SMD dataset description](https://github.com/NetManAIOps/OmniAnomaly/blob/7fb0e0acf89ea49908896bcc9f9e80fcfff6baf4/README.md).
- [Original OmniAnomaly paper](https://netman.aiops.org/wp-content/uploads/2019/08/OmniAnomaly_camera-ready.pdf).
- [2026 SMD protocol re-audit](https://arxiv.org/abs/2603.18985), used only to corroborate the common-normal-train and nominal one-minute conventions; it does not override the primary raw-file provenance.
