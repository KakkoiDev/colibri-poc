# Benchmark results

OS file cache uncontrolled; no cold-storage claim. Fresh KV per request.

| Variant | Median tok/s | Paired speedup | Exact tokens | Failed rounds |
|---|---:|---:|---|---:|
| baseline | 197.94770999993935 | 1.0 | True | 0 |
| allocator-256mb | 197.6176778263249 | 0.993920359186797 | True | 0 |
| allocator-off | 194.7500655786713 | 0.9902000542254463 | True | 0 |
| group-0 | 190.9658365430684 | 0.964728698013869 | True | 0 |
| group-128 | 198.37537541665918 | 0.9976754838393157 | True | 0 |
| group-256 | 197.18804183191884 | 0.9986203883041086 | True | 0 |
| group-32 | 198.48825852864223 | 0.9985697813107554 | True | 0 |
| resident-compiled-fused | 199.65035171511883 | 1.0086014721523173 | True | 0 |
| resident-compiled | 198.14949517774426 | 0.9980614601648696 | True | 0 |
| resident-fused | 195.55031372074143 | 0.9937807619258893 | True | 0 |

Output mismatches need quality investigation; they are not automatically a quality regression.
Unequal output lengths can confound throughput. Inspect raw rows and finish reasons.
