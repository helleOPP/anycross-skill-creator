# LarkBase (Bitable) in AnyCross

## Contents

- [Field formats](#field-formats)
- [The extract() helper family](#the-extract-helper-family)
- [Filters](#filters)
- [Writing records](#writing-records)

## Field formats

LarkBase reads and writes the same field in different shapes. This asymmetry causes most of the runtime errors in these flows.

| Field type | Read shape | Write shape |
|---|---|---|
| Text / RichText | `[{text, type}]` | plain string |
| Number | plain number | number |
| SingleSelect | plain string | string |
| MultiSelect | array of strings | array of strings |
| Formula / Lookup | `{type: N, value: [...]}` | read-only |
| Person | `[{name, en_name, id, email}]` | **pass the raw array through unchanged** |
| SingleLink / DuplexLink | `{link_record_ids: ["recXXX"]}` | `["recXXX"]` |
| URL | `{link, text}` | `{link: "url", text: "label"}` |
| DateTime | timestamp ms (number) | timestamp ms (number) |
| Checkbox | boolean | boolean |

Three of these have sharp edges worth stating outright:

- **Person**: the instinct is to `extract()` it into a name string. That fails — LarkBase wants the object array back. Pass `f['<PersonField>'] || []` straight through.
- **URL**: writing a plain string returns `URLFieldConvFail`. It needs the `{link, text}` object even when link and text are identical.
- **Formula/Lookup**: the `{type: N, value: [...]}` wrapper nests the real value one level down, and `N` varies by the underlying type. `extract()` below unwraps it.

## The extract() helper family

Paste these into script nodes that read Bitable records. They exist because a Bitable record's field values are polymorphic — the same reading code has to survive a text field, a lookup wrapper, and a null.

```javascript
function extract(val) {
  if (val === null || val === undefined) return '';
  if (typeof val === 'string') return val;
  if (typeof val === 'number') return String(val);
  if (typeof val === 'boolean') return val ? 'Yes' : 'No';
  if (Array.isArray(val)) {
    if (val.length === 0) return '';
    var f = val[0];
    if (typeof f === 'string') return val.join(', ');
    if (f && f.text !== undefined) return val.map(function(v) { return v.text || ''; }).join('');
    if (f && f.name !== undefined) return val.map(function(v) { return v.name || ''; }).join(', ');
    return '';
  }
  if (typeof val === 'object') {
    // Formula / lookup wrapper: {type: N, value: [...]}
    if (val.type !== undefined && Array.isArray(val.value)) {
      var inner = val.value;
      if (inner.length === 0) return '';
      var fi = inner[0];
      if (typeof fi === 'number') return String(fi);
      if (typeof fi === 'string') return fi;
      if (fi && fi.text !== undefined) return inner.map(function(v) { return v.text || ''; }).join('');
      return String(fi);
    }
    if (val.text !== undefined) return String(val.text);
    if (val.value !== undefined) return String(val.value);
    return '';
  }
  return String(val);
}

// Link fields: check link_record_ids first, the array form is the fallback
function extractLink(val) {
  if (!val) return '';
  if (val.link_record_ids && val.link_record_ids.length > 0) return val.link_record_ids[0];
  if (Array.isArray(val) && val.length > 0) return val[0].record_id || val[0].id || '';
  return '';
}

// 2760 -> "2,760"
function fmt(val) {
  var num = Number(val) || 0;
  return num.toFixed(0).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

// Timestamp ms -> "dd/mm/yyyy" at a fixed UTC offset.
// AnyCross script nodes run in UTC, so pass the offset your business day uses:
// 7 for Asia/Ho_Chi_Minh, 8 for Asia/Kuala_Lumpur.
function fmtDate(val, tzOffsetHours) {
  if (!val) return '';
  var ts;
  if (typeof val === 'number') ts = val;
  else if (val.type !== undefined && Array.isArray(val.value) && val.value.length > 0) ts = val.value[0];
  else ts = Number(val);
  if (!ts) return '';
  var d = new Date(ts + (tzOffsetHours || 0) * 3600 * 1000);
  return String(d.getUTCDate()).padStart(2, '0') + '/' +
         String(d.getUTCMonth() + 1).padStart(2, '0') + '/' +
         d.getUTCFullYear();
}
```

Field names in `f['...']` must match the Base exactly, including case and underscores. This is a common silent failure: a wrong name yields `undefined`, `extract()` politely returns `''`, and the flow writes a blank instead of erroring. When a template or a live Base is available, list the real field names rather than inferring them from the business description.

## Filters

```python
def filter_record_id(spel_expr):
    """Fetch one record by its Record Id."""
    return {"type": "object", "value": {
        "conjunction": s("and"),
        "conditions": {"type": "array", "value": [
            {"type": "object", "value": {
                "field_name": s("Record Id"),
                "operator":   s("is"),
                "value": {"type": "array", "value": [spel_expr]}
            }}
        ]}
    }}

def filter_link_contains(field_name, spel_expr):
    """Fetch child rows whose link field points at a parent record_id."""
    return {"type": "object", "value": {
        "conjunction": s("and"),
        "conditions": {"type": "array", "value": [
            {"type": "object", "value": {
                "field_name": s(field_name),
                "operator":   s("contains"),
                "value": {"type": "array", "value": [spel_expr]}
            }}
        ]}
    }}
```

Operators seen in exports: `is`, `isNot`, `contains`, `doesNotContain`, `isEmpty`, `isNotEmpty`, `isGreater`, `isLess`. `conjunction` is `and` or `or`.

An empty `conditions` array does not mean "match nothing" — it returns everything. If a filter is meant to be conditional, build it conditionally in Python rather than emitting an empty condition list.

## Writing records

Batch create (v2.7, `records` param) wants an array of `{fields: {...}}`:

```javascript
// inside a script node, building the payload for the bitable node
var records = rows.map(function (r) {
  return {
    fields: {
      '<TextField>':     r.name,                          // text -> string
      '<NumberField>':   Number(r.amount) || 0,           // number
      '<DateField>':     r.ts,                            // datetime -> ms
      '<LinkField>':     r.parentRecordIds || [],         // link -> ["recXXX"]
      '<PersonField>':   r.personRaw || [],               // person -> raw array, NOT extract()ed
      '<UrlField>':      {link: r.url, text: 'Open'}      // url -> {link, text}, NOT a string
    }
  };
});
return { records: records };
```

Then the bitable node's `records` parameter is a spel pointing at `$.script-N.result.records`.

`ignore_consistency_check: true` is what the exports use for batch writes; it trades a consistency guarantee for throughput and is the norm here.
