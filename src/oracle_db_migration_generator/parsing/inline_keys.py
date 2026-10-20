"""Use verified grammar spans to separate inline index-backed table keys."""
from ..model.identity import Identifier
from .statements import quote_identifier


def inline_backing_keys(root,text):
    records=[];pending=[root]
    while pending:
        node=pending.pop()
        if type(node).__name__=='Column_definitionContext':
            selected=[]
            for key in node.inline_constraint():
                state=key.constraint_state()
                terminal=key.KEY() or key.UNIQUE()
                if terminal is None or state is None or not state.using_index_clause(): continue
                name=key.constraint_name()
                column=node.column_name().getText()
                boundary=terminal.symbol.stop+1
                definition=(text[key.start.start:boundary]+'('+quote_identifier(Identifier.parse(column).effective_name)+')'+
                            text[boundary:key.stop.stop+1])
                selected.append((key,{'column':column,'name':name.getText() if name else None,'definition':definition}))
            if selected:
                definition=text[node.start.start:node.stop.stop+1]
                for key,_ in sorted(selected,key=lambda item:item[0].start.start,reverse=True):
                    begin,end=key.start.start-node.start.start,key.stop.stop+1-node.start.start
                    definition=definition[:begin]+definition[end:]
                for _,record in selected:
                    record['column_definition']=definition.rstrip();records.append(record)
        pending.extend(getattr(node,'children',None) or ())
    return records
