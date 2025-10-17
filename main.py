# main.py
front_r = rectify_card(front)
c_front = measure_centering(front_r)
c_front['meets_psa10'] = meets_tolerance(c_front['left'], c_front['right'], c_front['top'], c_front['bottom'], FRONT_TOL)


surface_front = surface_heuristics(front_r)


c_back = None
surface_back = None
if body.back_url:
back = url_to_bgr(body.back_url)
back_r = rectify_card(back)
c_back = measure_centering(back_r)
c_back['meets_psa10'] = meets_tolerance(c_back['left'], c_back['right'], c_back['top'], c_back['bottom'], BACK_TOL)
surface_back = surface_heuristics(back_r)


# Simple grade heuristic: start at 10, apply deductions
grade = 10
reasons = []
# Centering checks
if not c_front['meets_psa10']:
reasons.append('Front centering outside PSA10 tolerance')
grade = min(grade, 9)
if c_back and not c_back['meets_psa10']:
reasons.append('Back centering outside PSA10 tolerance')
grade = min(grade, 9)
# Edge whitening heuristic
ew = surface_front['edge_whitening_pct']
if ew > 0.5:
grade = min(grade, 9)
reasons.append(f'Edge whitening ~{ew:.1f}% perimeter pixels')
if surface_back:
ew2 = surface_back['edge_whitening_pct']
if ew2 > 0.5:
grade = min(grade, 9)
reasons.append(f'Back edge whitening ~{ew2:.1f}%')
# Quality warnings reduce confidence
warnings = []
warnings += surface_front['warnings']
if surface_back:
warnings += surface_back['warnings']


# Confidence: naive baseline 0.65, lower with warnings, raise with clean signals
conf = 0.65
conf -= 0.05*len(warnings)
conf = max(0.2, min(0.9, conf))


return {
'centering': {
'front': c_front,
'back': c_back or None
},
'surface': {
'front': surface_front,
'back': surface_back or None
},
'grade_estimate': {
'pred': f'PSA {grade}',
'confidence': round(conf, 2),
'reasons': reasons or ['Strong centering and minimal visible surface issues']
},
'thresholds': {
'front_10': '55/45',
'back_10': '75/25'
}
}