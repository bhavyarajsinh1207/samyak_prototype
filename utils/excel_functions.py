# MultipleFiles/utils/excel_functions.py
import pandas as pd
import numpy as np
from typing import Any

def _is_numberish(x: Any) -> bool:
    """Checks if a value can be converted to a float."""
    try:
        float(x)
        return True
    except (ValueError, TypeError):
        return False

def _resolve_arg(arg: str, df: pd.DataFrame):
    """
    Resolves an argument from an Excel-like expression.
    Can be a column name, a literal (string, number, boolean), or a NULL.
    """
    arg = arg.strip()
    if arg.upper() == 'NULL':
        return pd.Series([np.nan]*len(df), index=df.index) # Return a Series of NaNs
    if arg.startswith('"') and arg.endswith('"'):
        return arg.strip('"')
    if arg.startswith("'") and arg.endswith("'"):
        return arg.strip("'")
    if arg in df.columns:
        return df[arg]
    try:
        # Try converting to number (int or float)
        if '.' in arg:
            return float(arg)
        else:
            return int(arg)
    except ValueError:
        pass # Not a simple number
    if arg.lower() in ('true','false'):
        return True if arg.lower() == 'true' else False
    try:
        # Try evaluating as a pandas expression (e.g., 'column1 > column2')
        res = df.eval(arg)
        return res
    except Exception:
        # If all else fails, treat as a literal string
        return arg

def apply_excel_function(expr: str, df: pd.DataFrame):
    """
    Applies an Excel-like function expression to a DataFrame.
    Supports SUM, AVERAGE, COUNT, MIN, MAX, CONCAT, IF.
    """
    e = expr.strip()
    if e.startswith('='):
        e = e[1:].strip()

    # Check if it's a function call (e.g., SUM(A,B))
    if '(' in e and e.endswith(')'):
        fname_end_idx = e.find('(')
        fname = e[:fname_end_idx].strip().upper()
        inner = e[fname_end_idx+1:-1]

        # Parse arguments, handling commas inside quoted strings
        args = []
        cur = ''
        in_quote = False
        for ch in inner:
            if ch in ('"', "'"):
                in_quote = not in_quote
                cur += ch
            elif ch == ',' and not in_quote:
                args.append(cur.strip())
                cur = ''
            else:
                cur += ch
        if cur.strip(): # Add the last argument
            args.append(cur.strip())

        resolved_args = [_resolve_arg(a, df) for a in args if a!='']

        # Determine if any argument is a pandas Series (column)
        has_series_arg = any(isinstance(r, pd.Series) for r in resolved_args)

        if fname == 'SUM':
            if has_series_arg:
                s = pd.Series(0, index=df.index, dtype=float)
                for r in resolved_args:
                    if isinstance(r, pd.Series):
                        s = s.add(pd.to_numeric(r, errors='coerce').fillna(0), fill_value=0)
                    else:
                        # Add scalar to all elements of the Series
                        s = s.add(float(r) if _is_numberish(r) else 0, fill_value=0)
                return s
            else:
                return sum(float(r) for r in resolved_args if _is_numberish(r))

        elif fname in ('AVERAGE', 'AVG', 'MEAN'):
            if has_series_arg:
                # Collect all arguments as Series, converting scalars to Series
                series_list = []
                for r in resolved_args:
                    if isinstance(r, pd.Series):
                        series_list.append(pd.to_numeric(r, errors='coerce'))
                    elif _is_numberish(r):
                        series_list.append(pd.Series(float(r), index=df.index))
                    else:
                        series_list.append(pd.Series(np.nan, index=df.index))
                stacked = pd.concat(series_list, axis=1)
                return stacked.mean(axis=1)
            else:
                nums = [float(r) for r in resolved_args if _is_numberish(r)]
                return sum(nums) / len(nums) if nums else 0

        elif fname == 'COUNT':
            if len(resolved_args) == 1 and isinstance(resolved_args[0], pd.Series):
                return int(resolved_args[0].dropna().shape[0])
            else:
                return sum(1 for r in resolved_args if r is not None and not (isinstance(r, float) and np.isnan(r)))

        elif fname == 'MIN':
            if has_series_arg:
                series_list = []
                for r in resolved_args:
                    if isinstance(r, pd.Series):
                        series_list.append(pd.to_numeric(r, errors='coerce'))
                    elif _is_numberish(r):
                        series_list.append(pd.Series(float(r), index=df.index))
                    else:
                        series_list.append(pd.Series(np.nan, index=df.index))
                stacked = pd.concat(series_list, axis=1)
                return stacked.min(axis=1)
            else:
                return min(float(r) for r in resolved_args if _is_numberish(r))

        elif fname == 'MAX':
            if has_series_arg:
                series_list = []
                for r in resolved_args:
                    if isinstance(r, pd.Series):
                        series_list.append(pd.to_numeric(r, errors='coerce'))
                    elif _is_numberish(r):
                        series_list.append(pd.Series(float(r), index=df.index))
                    else:
                        series_list.append(pd.Series(np.nan, index=df.index))
                stacked = pd.concat(series_list, axis=1)
                return stacked.max(axis=1)
            else:
                return max(float(r) for r in resolved_args if _is_numberish(r))

        elif fname == 'CONCAT':
            if has_series_arg:
                parts = []
                for r in resolved_args:
                    if isinstance(r, pd.Series):
                        parts.append(r.astype(str).fillna(''))
                    else:
                        parts.append(pd.Series(str(r), index=df.index))
                # Summing strings in pandas concatenates them element-wise
                return sum(parts)
            else:
                return ''.join(str(r) for r in resolved_args)

        elif fname == 'IF':
            if len(resolved_args) < 3:
                raise ValueError('IF requires 3 arguments: IF(condition, true_val, false_val)')

            # The condition might be a string expression or a resolved boolean Series/scalar
            cond_raw_str = args[0] # Use original string for eval
            try:
                cond = df.eval(cond_raw_str)
            except Exception:
                # If eval fails, assume the first resolved_arg is the condition
                cond = resolved_args[0]
                if not isinstance(cond, pd.Series):
                    cond = pd.Series(bool(cond), index=df.index) # Convert scalar to Series

            true_val = resolved_args[1]
            false_val = resolved_args[2]

            # Ensure true_val and false_val are Series for element-wise operation
            if not isinstance(true_val, pd.Series):
                true_val = pd.Series(true_val, index=df.index)
            if not isinstance(false_val, pd.Series):
                false_val = pd.Series(false_val, index=df.index)

            return pd.Series(np.where(cond, true_val, false_val), index=df.index)

        else:
            # If it's not a recognized function, try to evaluate the whole expression
            # as a pandas expression (e.g., 'column1 + column2')
            try:
                res = df.eval(e)
                return res
            except Exception as ee:
                raise ValueError(f'Unsupported function or syntax: {fname} — {ee}')
    else:
        # If it's not a function call, just resolve the single argument
        return _resolve_arg(e, df)
