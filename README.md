# Exam Server

## todo 
- restrict exam-server domain `exam.laurel.informatik.uni-freiburg.de` to pool room ip addresses
- restrict pool image internet access to these domains: `{exam,auth}.laurel.informatik.uni-freiburg.de`. Notice that `exam.laurel.informatik.uni-freiburg.de` needs to be accessable on port `443` (HTTPS)  and `2223` (SSH).
- replace `skel` directory with _current_ exam files on `ahumoa:/teaching-server/laurel/exam-server/skel` (no need to restart exam-server when updating files in `skel` directory)
- download the `cli` for some specific exam, after changing env variables and restarting exam-server, here from `exam.laurel.informatik.uni-freiburg.de/cli/download`) and autostart it in the pool image.