OUT='/home/user/antonio-junior-hub-pessoal/tools/legendas/'
# expressões (time = quadro atual do título; comp.RenderEnd = último quadro do título)
POP_IN  = "(1-(1-min(time,7)/7)^3) + 0.12*sin(min(time,7)/7*3.14159)"
OUT_K   = "min(1, max(0, (comp.RenderEnd - time)/5))"
SLIDE_IN= "(1-(1-min(time,9)/9)^3)"

def textplus(name, extra, text):
    return f'''		{name} = TextPlus {{
			CtrlWZoom = false,
			Inputs = {{
				GlobalOut = Input {{ Value = 119, }},
				Width = Input {{ Value = 1080, }},
				Height = Input {{ Value = 1920, }},
				UseFrameFormatSettings = Input {{ Value = 1, }},
				StyledText = Input {{ Value = "{text}", }},
				Font = Input {{ Value = "Montserrat", }},
				Style = Input {{ Value = "Bold", }},
				Size = Input {{ Value = 0.075, }},
				VerticalJustificationNew = Input {{ Value = 3, }},
				HorizontalJustificationNew = Input {{ Value = 3, }},
				Center = Input {{ Value = {{ 0.5, 0.28 }}, }},
				Red1 = Input {{ Value = 1, }},
				Green1 = Input {{ Value = 1, }},
				Blue1 = Input {{ Value = 1, }},
{extra}			}},
			ViewInfo = OperatorInfo {{ Pos = {{ 0, 0 }} }},
		}},
'''
OUTLINE='''				Enabled2 = Input { Value = 1, },
				ElementShape2 = Input { Value = 1, },
				Thickness2 = Input { Value = 0.06, },
				Red2 = Input { Value = 0, },
				Green2 = Input { Value = 0, },
				Blue2 = Input { Value = 0, },
'''
BOX='''				Enabled3 = Input { Value = 1, },
				ElementShape3 = Input { Value = 2, },
				Level3 = Input { Value = 1, },
				ExtendHorizontal3 = Input { Value = 0.22, },
				ExtendVertical3 = Input { Value = 0.14, },
				Round3 = Input { Value = 0.35, },
				Red3 = Input { Value = 0.788, },
				Green3 = Input { Value = 0.635, },
				Blue3 = Input { Value = 0.153, },
'''
def transform(src, size_expr, center_expr=None):
    c = f'''				Center = Input {{ Value = {{ 0.5, 0.5 }}, Expression = "{center_expr}", }},\n''' if center_expr else ''
    return f'''		Anim = Transform {{
			CtrlWZoom = false,
			Inputs = {{
				Size = Input {{ Value = 1, Expression = "{size_expr}", }},
{c}				Input = Input {{ SourceOp = "{src}", Source = "Output", }},
			}},
			ViewInfo = OperatorInfo {{ Pos = {{ 110, 0 }} }},
		}},
'''
def macro(name, tools, dark=False, box=False):
    ins=[('Texto','StyledText','Texto',None),('Fonte','Font',None,'FontGroup'),('Estilo','Style',None,'FontGroup'),
         ('Tamanho','Size','Tamanho',None),('Posicao','Center','Posição',None),
         ('CorR','Red1','Cor do texto',1),('CorG','Green1',None,1),('CorB','Blue1',None,1)]
    if box: ins+=[('CaixaR','Red3','Cor da caixa',2),('CaixaG','Green3',None,2),('CaixaB','Blue3',None,2)]
    lines=[]
    for i,(k,src,label,grp) in enumerate(ins,1):
        extra=''
        if label: extra+=f' Name = "{label}",'
        if isinstance(grp,int): extra+=f' ControlGroup = {grp},'
        lines.append(f'\t\t\t\tInput{i} = InstanceInput {{ SourceOp = "Texto", Source = "{src}",{extra} }},')
    return f'''{{
	Tools = ordered() {{
		{name} = MacroOperator {{
			CtrlWZoom = false,
			NameSet = true,
			Inputs = ordered() {{
{chr(10).join(lines)}
			}},
			Outputs = {{
				MainOutput1 = InstanceOutput {{ SourceOp = "Anim", Source = "Output", }},
			}},
			ViewInfo = GroupInfo {{ Pos = {{ 0, 0 }} }},
			Tools = ordered() {{
{tools}			}},
		}},
	}},
	ActiveTool = "{name}"
}}
'''
pop = macro('NJ_Legenda_Pop', textplus('Texto', OUTLINE, 'SUA LEGENDA AQUI') + transform('Texto', f"({POP_IN}) * {OUT_K}"))
dest = macro('NJ_Legenda_Destaque', textplus('Texto', BOX.replace('Red1','x'), 'Sua legenda aqui').replace('Red1 = Input { Value = 1, }','Red1 = Input { Value = 0.05, }').replace('Green1 = Input { Value = 1, }','Green1 = Input { Value = 0.05, }').replace('Blue1 = Input { Value = 1, }','Blue1 = Input { Value = 0.06, }')
             + transform('Texto', OUT_K, f"Point(0.5, 0.5 - 0.04*(1-{SLIDE_IN}))"), box=True)
typ = textplus('Texto', OUTLINE + '				End = Input { Value = 1, Expression = "min(1, time/(max(comp.RenderEnd,1)*0.6))", },\n', 'Sua legenda aqui')
dig = macro('NJ_Legenda_Digitando', typ + transform('Texto', OUT_K))
for fn,s in [('NJ_Legenda_Pop.setting',pop),('NJ_Legenda_Destaque.setting',dest),('NJ_Legenda_Digitando.setting',dig)]:
    open(OUT+fn,'w').write(s)
print('ok')
