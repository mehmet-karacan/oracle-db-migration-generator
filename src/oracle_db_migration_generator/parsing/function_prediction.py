"""Schema Compare fonksiyon çağrısında belirli grammar dallarını doğrudan seçer.

Argümanlar mevcut grammar tarafından tamamen okunur. SQL metni, token ve
parse ağacındaki düğümler değiştirilmez. Diğer kararlar ANTLR'a bırakılır.

Author: Mehmet KARACAN
Date: 2026-11-09
"""
from antlr4.atn.ParserATNSimulator import ParserATNSimulator


class FunctionPrediction(ParserATNSimulator):
    """Sabit grammar'ın iç içe fonksiyonlarda gereksiz ileri bakmasını önler.

    Author: Mehmet KARACAN
    Date: 2026-11-09
    """
    def __init__(self,parser,*args):
        super().__init__(parser,*args)
        self.string_kinds=frozenset((parser.TO_CHAR,parser.NVL))
        self.numeric_kinds=frozenset((parser.SUM,parser.COUNT,parser.AVG,parser.MIN,
                                     parser.MAX,parser.ROUND,parser.LEAST,parser.GREATEST))
        expected={2575:parser.RULE_unary_expression_core,2614:parser.RULE_standard_function,
                  2603:parser.RULE_string_function,2609:parser.RULE_string_function,
                  2969:parser.RULE_general_element_part,2966:parser.RULE_general_element}
        if any(self.atn.decisionToState[key].ruleIndex!=value for key,value in expected.items()):
            raise RuntimeError('PINNED_FUNCTION_RULE_DRIFT')
        self.function_calls={}

    def function_kind(self,input):
        """Yalnız özel grammar dalıyla aynı biçimdeki yerleşik çağrıyı seçer."""
        parser=self.parser;kind=input.LA(1)
        if input.LA(2)!=parser.LEFT_PAREN:return 0
        if kind in self.numeric_kinds:return 2
        if kind not in self.string_kinds:return 0
        index=input.index
        if index in self.function_calls:return self.function_calls[index]
        arguments=[[]];depth=0;at=2;valid=False
        while input.LA(at)!=-1:
            token=input.LT(at)
            if token.type==parser.LEFT_PAREN:depth+=1
            elif token.type==parser.RIGHT_PAREN:
                depth-=1
                if depth==0:
                    valid=input.LA(at+1) not in {parser.PERIOD,parser.OVER,parser.KEEP}
                    break
            if depth==1 and token.text=='=>':break
            if depth==1 and token.type==parser.COMMA:arguments.append([])
            elif at>2:arguments[-1].append(token.text)
            at+=1
        if valid and all(arguments):
            if kind==parser.NVL:valid=len(arguments)==2
            else:
                valid=(1<=len(arguments)<=3 and all(len(arg)==1 and "'" in arg[0] for arg in arguments[1:]))
        else:valid=False
        result=1 if valid else 0
        self.function_calls[index]=result
        return result

    def adaptivePredict(self,input,decision,outerContext):
        parser=self.parser
        if decision==2969:
            # Eski Oracle dış birleştirme işareti fonksiyon argümanı değildir.
            if (input.LA(1)==parser.LEFT_PAREN and input.LA(2)==parser.PLUS_SIGN
                    and input.LA(3)==parser.RIGHT_PAREN):
                return 2
            return 1 if input.LA(1)==parser.LEFT_PAREN else 2
        if decision==2966 and input.LA(1)!=parser.PERIOD:
            return 2
        kind=self.function_kind(input) if decision in {2575,2614,2603,2609} else 0
        if kind:
            if decision==2575:return 3
            if decision==2614:return kind
            # TO_CHAR ve TO_DATE argümanı tek fonksiyonsa aynı alt ağaç seçilir.
            # Aritmetik devam ediyorsa expression dalı bütün ifadeyi doğrular.
            depth=0;at=2
            while input.LA(at)!=-1:
                kind=input.LA(at)
                if kind==parser.LEFT_PAREN:depth+=1
                elif kind==parser.RIGHT_PAREN:
                    depth-=1
                    if depth==0:
                        return 2 if input.LA(at+1) in {parser.COMMA,parser.RIGHT_PAREN,parser.DEFAULT} else 3
                at+=1
        return super().adaptivePredict(input,decision,outerContext)
