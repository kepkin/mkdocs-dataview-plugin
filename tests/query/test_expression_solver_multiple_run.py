from mkdocs_dataview.query.solvers import ExpressionSolverService

def test(subtests):
    query = r"""metadata.a + metadata.b > 10"""
    tests = [
        [
            False,
            {
                "metadata": {
                    "a": 1,
                    "b": 2,
                }
            },
        ],
        [
            True,
            {
                "metadata": {
                    "a": 1,
                    "b": 10
                }
            },
        ],
    ]

    sut = ExpressionSolverService(query)
    for i, (expected_result, identifiers) in enumerate(tests):
        with subtests.test(msg=f"Interpreter test line {i+15} {query}"):
            res = sut.solve(identifiers)
            print(res)
            assert expected_result == res
